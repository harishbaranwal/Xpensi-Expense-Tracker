"""
Utilities for managing expense lists and filters

This module contains specialized functions for:
- Applying filters to expenses
- Calculating expense statistics
- Detecting active filters
- Building complete context for the expense list
"""

from django.db.models import Sum
from ..models import Expense
from ..forms import ExpenseFilterForm


def apply_expense_filters(expenses, filter_form):
    """
    Apply all filters to an expenses QuerySet
    
    Args:
        expenses: Base expenses QuerySet
        filter_form: Validated filter form
    
    Returns:
        tuple: (expenses_filtered, active_period_info, period_dates)
    """
    # Import here to avoid circular imports
    from .util_dashboard import get_period_dates
    
    active_period_info = None
    period_dates = None
    
    if not filter_form.is_valid():
        return expenses, active_period_info, period_dates
    
    # Predefined period filter (reusing existing logic)
    period = filter_form.cleaned_data.get('period')
    if period:
        start_date, end_date, period_label = get_period_dates(period)
        expenses = expenses.filter(date__gte=start_date, date__lte=end_date)
        active_period_info = period_label
        period_dates = (start_date, end_date)
    
    # Category filter
    category = filter_form.cleaned_data.get('category')
    if category:
        expenses = expenses.filter(category=category)
    
    # Custom date filters (only if no predefined period)
    if not period:
        date_from = filter_form.cleaned_data.get('date_from')
        if date_from:
            expenses = expenses.filter(date__gte=date_from)
        
        date_to = filter_form.cleaned_data.get('date_to')
        if date_to:
            expenses = expenses.filter(date__lte=date_to)
    
    # Amount filters
    min_amount = filter_form.cleaned_data.get('min_amount')
    if min_amount:
        expenses = expenses.filter(amount__gte=min_amount)
    
    max_amount = filter_form.cleaned_data.get('max_amount')
    if max_amount:
        expenses = expenses.filter(amount__lte=max_amount)
    
    return expenses, active_period_info, period_dates


def calculate_expense_statistics(expenses):
    """
    Calculate statistics for an expenses QuerySet
    
    Args:
        expenses: Expenses QuerySet
    
    Returns:
        dict: Calculated statistics
    """
    total_filtered = expenses.aggregate(total=Sum('amount'))['total'] or 0
    count_filtered = expenses.count()
    
    return {
        'total_filtered': total_filtered,
        'count_filtered': count_filtered,
    }


def detect_active_filters(filter_form):
    """
    Detect whether the form has active filters
    
    Args:
        filter_form: Validated filter form
    
    Returns:
        bool: True if there are active filters
    """
    if not filter_form.is_valid():
        return False
    
    return any([
        filter_form.cleaned_data.get('period'),
        filter_form.cleaned_data.get('category'),
        filter_form.cleaned_data.get('date_from'),
        filter_form.cleaned_data.get('date_to'),
        filter_form.cleaned_data.get('min_amount'),
        filter_form.cleaned_data.get('max_amount'),
    ])


def get_expense_list_context(user, request_params):
    """
    Main function that generates the complete context for the expense list
    
    Args:
        user: Current user
        request_params: GET parameters from the request
    
    Returns:
        dict: Complete context for the template
    """
    # Get all user expenses
    expenses = Expense.objects.filter(user=user).select_related('category')
    
    # Initialize filter form
    filter_form = ExpenseFilterForm(request_params or None)
    
    # Apply filters
    expenses, active_period_info, period_dates = apply_expense_filters(expenses, filter_form)
    
    # Order by date (most recent first)
    expenses = expenses.order_by('-date')
    
    # Calculate statistics
    statistics = calculate_expense_statistics(expenses)
    
    # Detect active filters
    has_filters = detect_active_filters(filter_form)
    
    # Build context
    context = {
        'expenses': expenses,
        'has_filters': has_filters,
        'active_period_info': active_period_info,
        'period_dates': period_dates,
        'filter_form': filter_form,
        **statistics,  # total_filtered, count_filtered
    }
    
    return context 