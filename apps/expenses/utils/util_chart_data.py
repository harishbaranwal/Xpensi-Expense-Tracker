"""
Utilities for chart data preparation

This module contains specialized functions for:
- Preparing data for Chart.js
- Formatting data for doughnut charts
- Formatting data for line charts
"""

import json
from django.db.models import Sum
from django.db.models.functions import TruncDay


def prepare_chart_data(categories_summary, period_expenses):
    """
    Prepare data for Chart.js charts.
    
    Args:
        categories_summary: QuerySet with category summary
        period_expenses: QuerySet with expenses for the period
    
    Returns:
        dict: Data prepared for Chart.js in JSON format
    """
    # Data for doughnut chart (categories)
    chart_categories = list(categories_summary.values_list('category__name', flat=True))
    chart_amounts = list(categories_summary.values_list('total', flat=True))

    # Try to extract category colors when available. If the DB/queryset doesn't include
    # a 'category__color' value (older migrations), fall back to a default palette.
    default_palette = [
        '#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#06B6D4', '#F97316', '#F43F5E'
    ]
    try:
        chart_colors = list(categories_summary.values_list('category__color', flat=True))
        # If queryset returned empty colors or None entries, replace with default palette values
        if not any(chart_colors):
            chart_colors = [default_palette[i % len(default_palette)] for i in range(len(chart_categories))]
    except Exception:
        # values_list may raise if 'category__color' is not present on the queryset/model
        chart_colors = [default_palette[i % len(default_palette)] for i in range(len(chart_categories))]
    
    # Expenses per day (line chart)
    daily_expenses = period_expenses.annotate(
        day=TruncDay('date')
    ).values('day').annotate(
        total=Sum('amount')
    ).order_by('day')
    
    # Prepare data for line chart
    chart_dates = []
    chart_daily_amounts = []
    for expense in daily_expenses:
        chart_dates.append(expense['day'].strftime('%Y-%m-%d'))
        chart_daily_amounts.append(float(expense['total']))
    
    return {
        'chart_categories_json': json.dumps(chart_categories),
        'chart_amounts_json': json.dumps([float(amount) for amount in chart_amounts]),
        'chart_colors_json': json.dumps(chart_colors),
        'chart_dates_json': json.dumps(chart_dates),
        'chart_daily_amounts_json': json.dumps(chart_daily_amounts),
    } 