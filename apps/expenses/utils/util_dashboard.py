"""
Dashboard utilities and metrics calculations

This module contains all logic related to:
- Period and date calculations
- Dashboard metrics
- Complete dashboard context
"""

from datetime import datetime, timedelta
from django.db.models import Sum
from ..models import Expense, Budget


def get_period_dates(period):
    """
    Calculate start/end dates and label for the selected period
    
    Args:
        period (str): Selected period ('current_month', 'last_month', etc.)
    
    Returns:
        tuple: (start_date, end_date, period_label)
    """
    today = datetime.now().date()
    
    if period == 'current_month':
        start_date = today.replace(day=1)
        next_month = start_date.replace(month=start_date.month + 1) if start_date.month < 12 else start_date.replace(year=start_date.year + 1, month=1)
        end_date = next_month - timedelta(days=1)
        period_label = f"This month ({start_date.strftime('%B %Y').title()})"
        
    elif period == 'last_month':
        first_day_current = today.replace(day=1)
        end_date = first_day_current - timedelta(days=1)
        start_date = end_date.replace(day=1)
        period_label = f"Last month ({start_date.strftime('%B %Y').title()})"
        
    elif period == 'last_7_days':
        start_date = today - timedelta(days=7)
        end_date = today
        period_label = f"Last 7 days"
        
    elif period == 'last_30_days':
        start_date = today - timedelta(days=30)
        end_date = today
        period_label = f"Last 30 days"
        
    elif period == 'current_year':
        start_date = today.replace(month=1, day=1)
        end_date = today.replace(month=12, day=31)
        period_label = f"This year ({today.year})"
    
    else:  # Default: current_month
        start_date = today.replace(day=1)
        next_month = start_date.replace(month=start_date.month + 1) if start_date.month < 12 else start_date.replace(year=start_date.year + 1, month=1)
        end_date = next_month - timedelta(days=1)
        period_label = f"This month"
    
    return start_date, end_date, period_label


def calculate_dashboard_metrics(user, start_date, end_date, period=None):
    """
    Calculate all dashboard metrics for the specified period
    
    Args:
        user: Current user
        start_date: Period start date
        end_date: Period end date
        period: Selected period (to adjust daily average calculation)
    
    Returns:
        dict: Dictionary with all calculated metrics
    """
  
    period_expenses = Expense.objects.filter(
        user=user,
        date__gte=start_date,
        date__lte=end_date
    ).select_related('category')
    
    # Calcular métricas básicas del período
    period_total = period_expenses.aggregate(total=Sum('amount'))['total'] or 0
    period_expenses_count = period_expenses.count()
    
    # Calculate daily average
    # For current month, use only days elapsed up to today
    if period == 'current_month':
        today = datetime.now().date()
        # If we are in the current month, use days from the beginning of the month to today
        period_days = (today - start_date).days + 1
    else:
        # For other periods, use the full range
        period_days = (end_date - start_date).days + 1
    
    period_avg_daily = period_total / period_days if period_days > 0 else 0
    
    # Recent expenses for current user (independent from the selected period)
    recent_expenses = Expense.objects.filter(user=user).select_related('category').order_by('-date')[:10]
    
    # Expenses grouped by category for the selected period
    # Some installations may not have the Category.color field in DB (migrations not applied).
    # Detect field presence and build the queryset accordingly so we don't raise FieldError.
    from ..models import Category as _Category
    category_field_names = [f.name for f in _Category._meta.get_fields()]

    if 'color' in category_field_names:
        categories_summary = period_expenses.values('category__name', 'category__color').annotate(
            total=Sum('amount')
        ).order_by('-total')
    else:
        # Fallback: only include category name and totals (no color available)
        categories_summary = period_expenses.values('category__name').annotate(
            total=Sum('amount')
        ).order_by('-total')
    
    return {
        'period_total': period_total,
        'period_expenses_count': period_expenses_count,
        'period_avg_daily': period_avg_daily,
        'recent_expenses': recent_expenses,
        'categories_summary': categories_summary,
        # Para compatibilidad con template existente
        'monthly_total': period_total,
        'monthly_expenses_count': period_expenses_count,
        'avg_daily_expense': period_avg_daily,
    }


def get_dashboard_context(user, period):
    """
    Main function that combines all dashboard metrics
    
    Args:
        user: Current user
        period: Selected period
    
    Returns:
        dict: Complete context for the dashboard template
    """
    # Importar aquí para evitar imports circulares
    from .util_chart_data import prepare_chart_data
    
    # Get period dates
    start_date, end_date, period_label = get_period_dates(period)
    
    # Calculate metrics
    metrics = calculate_dashboard_metrics(user, start_date, end_date, period)
    
    # Filter period expenses for charts
    period_expenses = Expense.objects.filter(
        user=user,
        date__gte=start_date,
        date__lte=end_date
    ).select_related('category')
    
    # Prepare chart data
    chart_data = prepare_chart_data(metrics['categories_summary'], period_expenses)
    
    # Combine everything into the context
    context = {
        **metrics,
        **chart_data,
        'period_label': period_label,
        'selected_period': period,
    }
    
    # Add budget information
    budget_info = get_budget_info(user, metrics['period_total'])
    context.update(budget_info)
    
    return context


def get_budget_info(user, current_month_total):
    """
    Get the user's budget information in a simple way
    """
    try:
        budget = Budget.objects.get(user=user)
        
        # Calculate basic data
        percentage_used = budget.get_percentage_used(current_month_total)
        remaining_amount = budget.get_remaining_amount(current_month_total)
        status = budget.get_status_for_amount(current_month_total)
        
        # Determine color and message based on the status
        if status == 'safe':
            color_class = 'text-green-600 bg-green-50 border-green-200'
            icon = '✅'
            message = f"You're doing well! You have ₹{remaining_amount:.0f} remaining"
        elif status == 'warning':
            color_class = 'text-yellow-600 bg-yellow-50 border-yellow-200'
            icon = '⚠️'
            message = f"Careful! Only ₹{remaining_amount:.0f} left"
        elif status == 'critical':
            color_class = 'text-red-600 bg-red-50 border-red-200'
            icon = '🚨'
            message = f"Limit almost reached! Only ₹{remaining_amount:.0f} remaining"
        else:  # exceeded
            color_class = 'text-red-600 bg-red-50 border-red-200'
            icon = '🛑'
            excess = current_month_total - budget.monthly_limit
            message = f"Limit exceeded! You've overspent by ₹{excess:.0f}"
        
        return {
            'has_budget': True,
            'budget': budget,
            'budget_percentage_used': percentage_used,
            'budget_remaining': remaining_amount,
            'budget_status': status,
            'budget_color_class': color_class,
            'budget_icon': icon,
            'budget_message': message,
        }
        
    except Budget.DoesNotExist:
        return {
            'has_budget': False,
            'budget': None,
        } 