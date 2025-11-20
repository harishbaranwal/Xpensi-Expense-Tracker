"""
Utilities for CRUD operations and HTMX responses

This module contains specialized functions for:
- CRUD operations (Create, Read, Update, Delete)
- Specialized HTMX responses
- Consistent error handling
- Context builders for different operations
"""

from django.shortcuts import render
from django.contrib import messages
from django.shortcuts import redirect
from django.utils import timezone
from django.db.models import Sum
from django.conf import settings
import requests
from ..models import Expense, Budget

def get_expense_for_user(expense_id, user):
    """
    Get a specific expense ensuring it belongs to the current user

    Args:
        expense_id: Expense ID
        user: Current user

    Returns:
        Expense: Expense object or None if it doesn't exist/doesn't belong to the user

    Raises:
        Expense.DoesNotExist: If the expense doesn't exist or doesn't belong to the user
    """
    try:
        return Expense.objects.get(id=expense_id, user=user)
    except Expense.DoesNotExist:
        raise Expense.DoesNotExist("The expense does not exist or you don't have permission to access it")


def handle_expense_creation(form_data, user):
    """
    Handle creation of a new expense with form data

    Args:
        form_data: POST data from the form
        user: Current user

    Returns:
        tuple: (expense, form, is_valid)
    """
    from ..forms import ExpenseForm
    
    form = ExpenseForm(form_data)
    
    if form.is_valid():
        expense = form.save(commit=False)
        expense.user = user
        expense.save()
        
        # Check 90% budget alert
        check_budget_alert(user)
        
        return expense, form, True
    
    return None, form, False


def handle_expense_form_update(expense, form_data):
    """
    Handle updating an expense with form data

    Args:
        expense: Expense instance to update
        form_data: POST data from the form

    Returns:
        tuple: (updated_expense, form, is_valid)
    """
    from ..forms import ExpenseForm
    
    form = ExpenseForm(form_data, instance=expense)
    
    if form.is_valid():
        updated_expense = form.save()
        return updated_expense, form, True
    
    return expense, form, False


def handle_expense_deletion(expense_id, user):
    """
    Handle safe deletion of an expense

    Args:
        expense_id: ID of the expense to delete
        user: Current user

    Returns:
        tuple: (expense_data, is_deleted, error_message)
    """
    try:
        # Get the expense using existing helper function
        expense = get_expense_for_user(expense_id, user)
        
        # Store data for the confirmation message
        expense_data = {
            'amount': expense.amount,
            'category_name': expense.category.name,
            'description': expense.description or 'No description',
            'date': expense.date
        }
        
        # Delete the expense
        expense.delete()
        
        return expense_data, True, None
        
    except Expense.DoesNotExist:
        return None, False, "The expense does not exist or you don't have permission to delete it"


def build_add_expense_context(form=None):
    """
    Build context for the add expense form

    Args:
        form: Form instance (new or with errors)

    Returns:
        dict: Context for the template
    """
    from ..forms import ExpenseForm
    
    if form is None:
        form = ExpenseForm()
    
    return {
        'form': form
    }


def build_expense_edit_context(user, expense, form, request_params):
    """
    Build context to show after a successful edit

    Args:
        user: Current user
        expense: Updated expense
        form: Form used
        request_params: GET parameters of the request

    Returns:
        dict: Updated context with success message
    """
    # Import here to avoid circular imports
    from .util_expense_list import get_expense_list_context
    
    # Get updated list context
    context = get_expense_list_context(user, request_params)
    
    # Add specific information about the edit
    context.update({
        'edit_success': True,
        'expense_data': {
            'amount': expense.amount,
            'category_name': expense.category.name,
            'description': expense.description or 'No description',
            'date': expense.date
        },
        'edit_message': 'Expense updated successfully'
    })
    
    return context


def build_delete_success_context(user, expense_data, request_params):
    """
    Build context to show after a successful deletion

    Args:
        user: Current user
        expense_data: Deleted expense data
        request_params: GET parameters of the request

    Returns:
        dict: Updated context with success message
    """
    # Import here to avoid circular imports
    from .util_expense_list import get_expense_list_context
    
    # Get updated list context
    context = get_expense_list_context(user, request_params)
    
    # Add specific information about the deletion
    context.update({
        'delete_success': True,
        'expense_data': expense_data,
        'delete_message': 'Expense deleted successfully'
    })
    
    return context


def handle_expense_error_response(request, error_message):
    """
    Handle error responses consistently

    Args:
        request: Django request object
        error_message: Error message to display

    Returns:
        HttpResponse: Appropriate response depending on request type
    """
    if request.headers.get('HX-Request'):
        return render(request, 'expenses/partials/delete_error.html', {
            'error': error_message
        })
    
    messages.error(request, error_message)
    return redirect('expenses:expense_list')


def create_htmx_add_response(request, expense):
    """
    Create HTMX response for successful creation that auto-updates content

    Args:
        request: Django request object
        expense: Successfully created expense

    Returns:
        HttpResponse: Response with success message and update triggers
    """
    response = render(request, 'expenses/partials/expense_success.html', {
        'expense': expense,
        'message': 'Expense added successfully!'
    })
    
    # Add triggers to auto-update content
    # - refreshExpenseList: refresh the list if visible
    # - refreshDashboard: refresh dashboard metrics if visible
    response['HX-Trigger-After-Settle'] = 'refreshExpenseList, refreshDashboard'
    
    return response


def create_htmx_edit_response(request, context):
    """
    Create HTMX response for successful edit with trigger to close modal

    Args:
        request: Django request object
        context: Context for the template

    Returns:
        HttpResponse: Response with HX-Trigger-After-Swap header
    """
    response = render(request, 'expenses/partials/expense_list_content.html', context)
    response['HX-Trigger-After-Swap'] = 'closeEditModal'
    return response


def create_htmx_delete_response(request, context):
    """
    Create HTMX response for successful deletion

    Args:
        request: Django request object
        context: Context for the template

    Returns:
        HttpResponse: Response with updated list
    """
    return render(request, 'expenses/partials/expense_list_content.html', context)


def check_budget_alert(user):
    """
    Check if the user has reached or exceeded 90% of their budget
    and send a webhook to n8n if necessary

    Args:
        user: Current user
    """
    
    try:
        # Get the user's budget
        budget = Budget.objects.get(user=user)
        
        # Only proceed if alerts are enabled
        if not budget.email_alerts_enabled:
            return
        
        # Calculate current month expenses
        now = timezone.now()
        current_month_expenses = Expense.objects.filter(
            user=user,
            date__year=now.year,
            date__month=now.month
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Calculate percentage
        percentage = (current_month_expenses / budget.monthly_limit) * 100
        
        # Check if it reached or exceeded 90%
        if percentage >= 90:
            send_webhook_to_n8n(user, budget, current_month_expenses, percentage)
            
    except Budget.DoesNotExist:
        # User has no configured budget
        pass


def send_webhook_to_n8n(user, budget, current_spending, percentage):
    """
    Send a webhook to n8n with the budget alert data

    Args:
        user: User who exceeded the limit
        budget: User's Budget object
        current_spending: Current month's spending
        percentage: Percentage of the budget used
    """
    
    # Webhook functionality removed for local-only development
    # This function is disabled for simplified local setup
    return
    
    payload = {
        'user_id': user.id,
        'user_name': user.get_full_name() or user.username,
        'user_email': user.email,
        'budget_limit': float(budget.monthly_limit),
        'current_spending': float(current_spending or 0),
        'percentage': round(float(percentage), 2),
        'alert_type': 'budget_90_percent',
        'message': f'You have reached {percentage:.1f}% of your monthly budget',
        'timestamp': timezone.now().isoformat()
    }
    
    try:
        # Headers with Bearer Token for authentication
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {settings.N8N_WEBHOOK_TOKEN}'
        }
        
        response = requests.post(
            webhook_url,
            json=payload,
            timeout=10,  # 10 second timeout
            headers=headers
        )
        
        # Log result (optional)
        if response.status_code == 200:
            print(f"[SUCCESS] Webhook sent successfully for {user.username}")
        else:
            print(f"[WARNING] Webhook error: {response.status_code} - {response.text}")
            
    except requests.exceptions.RequestException as e:
        # Don't fail if the webhook fails - just log
        print(f"[ERROR] Error sending webhook: {e}")
        pass 