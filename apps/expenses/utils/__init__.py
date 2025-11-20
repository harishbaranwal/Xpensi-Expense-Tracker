"""
Modularized utils for the expenses application

This package contains utilities organized by responsibility:
- util_dashboard.py: Dashboard logic and metrics
- util_chart_data.py: Chart data preparation
- util_expense_list.py: Expense list and filters
- util_crud_operations.py: CRUD operations with HTMX

Recommended usage with specific imports:
    from apps.expenses.utils.util_dashboard import calculate_dashboard_metrics
    from apps.expenses.utils.util_crud_operations import handle_expense_creation
    from apps.expenses.utils.util_expense_list import get_expense_list_context
    from apps.expenses.utils.util_chart_data import prepare_chart_data

Why specific imports?
- Clearer and more explicit
- Better for IDEs and autocomplete
- Avoids circular imports
- Easier to maintain and debug
"""