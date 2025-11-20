from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Expense, Budget
from .forms import ExpenseForm, BudgetForm
# Imports específicos de utils modularizados
from .utils.util_dashboard import get_dashboard_context
from .utils.util_expense_list import get_expense_list_context
from .utils.util_crud_operations import (
    get_expense_for_user,
    handle_expense_creation,
    handle_expense_form_update,
    handle_expense_deletion,
    build_add_expense_context,
    build_expense_edit_context,
    build_delete_success_context,
    handle_expense_error_response,
    create_htmx_add_response,
    create_htmx_edit_response,
    create_htmx_delete_response
)


@login_required
def dashboard(request):
    """
    Display the main dashboard with expense metrics.
    Handles period filters with HTMX.
    """
    # Get the selected period from the filter
    period = request.GET.get('period', 'current_month')
    
    # Get all dashboard context using helper functions
    context = get_dashboard_context(request.user, period)
    
    # If HTMX request, return only metrics
    if request.headers.get('HX-Request'):
        return render(request, 'expenses/partials/dashboard_metrics.html', context)
    
    return render(request, 'expenses/dashboard.html', context)


@login_required
def expense_list(request):
    """
    Display the user's expense list with filters.
    Handles both normal and HTMX requests.
    """
    # Get all context using helper functions
    context = get_expense_list_context(request.user, request.GET)
    
    # Is it an HTMX request? Return only partial content
    if request.headers.get('HX-Request'):
        return render(request, 'expenses/partials/expense_list_content.html', context)
    
    # Normal request: return full page
    return render(request, 'expenses/expense_list.html', context)


@login_required
def add_expense(request):
    """
    Handles the creation of new expenses.
    Supports both traditional forms and HTMX modals.
    """
    if request.method == 'POST':
        # Handle expense creation using helper function
        expense, form, is_valid = handle_expense_creation(request.POST, request.user)
        
        # Valid form: HTMX response with success message
        if is_valid and request.headers.get('HX-Request'):
            return create_htmx_add_response(request, expense)
        
        # Valid form: normal redirect
        if is_valid:
            messages.success(request, 'Expense added successfully!')
            return redirect('expenses:dashboard')
        
        # Form with errors: show HTMX modal
        if request.headers.get('HX-Request'):
            return render(request, 'expenses/partials/add_expense_modal.html', {
                'form': form
            })
    
    else:
        # Get context using helper function
        context = build_add_expense_context()
        
        # Show form: HTMX modal or full page
        if request.headers.get('HX-Request'):
            return render(request, 'expenses/partials/add_expense_modal.html', context)
        
        return render(request, 'expenses/add_expense.html', context)


@login_required
def close_modal(request):
    """
    View to close HTMX modals.
    """
    return render(request, 'expenses/partials/empty.html')


@login_required
def delete_expense(request, expense_id):
    """
    Deletes a specific user's expense.
    Supports deletion via HTMX and traditional requests.
    """
    if request.method == 'DELETE':
        # Handle expense deletion using helper function
        expense_data, is_deleted, error_message = handle_expense_deletion(expense_id, request.user)
        
        # Successful deletion: HTMX response with updated list
        if is_deleted and request.headers.get('HX-Request'):
            context = build_delete_success_context(request.user, expense_data, request.GET)
            return create_htmx_delete_response(request, context)
        
        # Successful deletion: normal redirect
        if is_deleted:
            messages.success(request, f'Expense of ₹{expense_data["amount"]} deleted successfully')
            return redirect('expenses:expense_list')
        
        # Error in deletion: handle error response
        return handle_expense_error_response(request, error_message)


@login_required
def edit_expense(request, expense_id):
    """
    Allows editing an existing user's expense.
    Supports editing via HTMX modal and traditional forms.
    """
    try:
        # Get the expense using helper function
        expense = get_expense_for_user(expense_id, request.user)
        
        if request.method == 'POST':
            updated_expense, form, is_valid = handle_expense_form_update(expense, request.POST)
            
            # Valid form: HTMX response with updated list
            if is_valid and request.headers.get('HX-Request'):
                context = build_expense_edit_context(request.user, updated_expense, form, request.GET)
                return create_htmx_edit_response(request, context)
            
            # Valid form: normal redirect
            if is_valid:
                messages.success(request, f'Expense of ₹{updated_expense.amount} updated successfully')
                return redirect('expenses:expense_list')
            
            # Form with errors: show HTMX modal
            if request.headers.get('HX-Request'):
                return render(request, 'expenses/partials/edit_expense_modal.html', {
                    'form': form,
                    'expense': expense,
                    'form_errors': True
                })
            
        else:
            form = ExpenseForm(instance=expense)
            
        # Show form: HTMX modal or full page
        if request.headers.get('HX-Request'):
            return render(request, 'expenses/partials/edit_expense_modal.html', {
                'form': form,
                'expense': expense
            })
        
        return render(request, 'expenses/edit_expense.html', {
            'form': form,
            'expense': expense
        })
        
    except Expense.DoesNotExist:
        return handle_expense_error_response(
            request, 
            'The expense does not exist or you do not have permission to edit it.'
        )


@login_required
def manage_budget(request):
    """
    Simple view to configure the user's budget.
    """
    try:
        budget = Budget.objects.get(user=request.user)
    except Budget.DoesNotExist:
        budget = None
    
    if request.method == 'POST':
        form = BudgetForm(request.POST, instance=budget)
        if form.is_valid():
            budget = form.save(commit=False)
            budget.user = request.user
            budget.save()
            
            # HTMX response: reload dashboard
            if request.headers.get('HX-Request'):
                messages.success(request, 'Budget configured successfully!')
                response = render(request, 'expenses/partials/budget_success.html', {
                    'budget': budget
                })
                response['HX-Trigger'] = 'refreshDashboard'  # Reload metrics
                return response
            
            messages.success(request, 'Budget configured successfully!')
            return redirect('expenses:dashboard')
    else:
        form = BudgetForm(instance=budget)
    
    # HTMX modal or full page
    if request.headers.get('HX-Request'):
        return render(request, 'expenses/partials/budget_modal.html', {
            'form': form,
            'budget': budget
        })
    
    return render(request, 'expenses/budget.html', {
        'form': form,
        'budget': budget
    })



