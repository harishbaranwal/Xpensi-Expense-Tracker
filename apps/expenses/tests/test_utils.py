"""
Tests for expenses utilities

Covers critical functions for dashboard, filters, and CRUD
"""
import pytest
from datetime import datetime, date, timedelta
from decimal import Decimal
from django.contrib.auth.models import User
from apps.expenses.models import Category, Expense, Budget
from apps.expenses.utils.util_dashboard import (
    get_period_dates, 
    calculate_dashboard_metrics,
    get_budget_info
)
from apps.expenses.utils.util_expense_list import (
    calculate_expense_statistics,
    detect_active_filters
)
from apps.expenses.utils.util_crud_operations import (
    get_expense_for_user,
    handle_expense_creation
)
from apps.expenses.forms import ExpenseForm, ExpenseFilterForm


class TestDashboardUtils:
    """Tests for dashboard utilities"""
    
    def test_get_period_dates_current_month(self):
        """Test date calculations for current month"""
        start_date, end_date, period_label = get_period_dates('current_month')
        
        today = datetime.now().date()
        expected_start = today.replace(day=1)
        
        assert start_date == expected_start
        assert start_date.day == 1
        assert end_date.month == today.month
        assert "This month" in period_label
    
    def test_get_period_dates_last_7_days(self):
        """Test date calculations for last 7 days"""
        start_date, end_date, period_label = get_period_dates('last_7_days')
        
        today = datetime.now().date()
        expected_start = today - timedelta(days=7)
        
        assert start_date == expected_start
        assert end_date == today
        assert period_label == "Last 7 days"
    
    def test_get_period_dates_default(self):
        """Test default behavior (current month)"""
        start_date, end_date, period_label = get_period_dates('invalid_period')
        
        today = datetime.now().date()
        expected_start = today.replace(day=1)
        
        assert start_date == expected_start
        assert "This month" in period_label

    @pytest.mark.django_db
    def test_calculate_dashboard_metrics(self):
        """Test dashboard metrics calculation"""
        # Crear datos de test
        user = User.objects.create_user(username="testuser")
        category = Category.objects.create(name="Test", color="#FF0000")
        
        # Crear gastos para el período
        today = date.today()
        start_date = today.replace(day=1)
        end_date = today
        
        Expense.objects.create(
            user=user, category=category, 
            amount=Decimal('10.00'), date=today
        )
        Expense.objects.create(
            user=user, category=category, 
            amount=Decimal('20.00'), date=today
        )
        
        # Calcular métricas
        metrics = calculate_dashboard_metrics(user, start_date, end_date)
        
        assert metrics['period_total'] == Decimal('30.00')
        assert metrics['period_expenses_count'] == 2
        assert metrics['period_avg_daily'] > 0
        assert 'recent_expenses' in metrics
        assert 'categories_summary' in metrics


class TestBudgetUtils:
    """Tests for budget utilities"""
    
    @pytest.mark.django_db
    def test_get_budget_info_no_budget(self):
        """Test get_budget_info when user has no budget"""
        user = User.objects.create_user(username="testuser")
        
        budget_info = get_budget_info(user, Decimal('500.00'))
        
        assert budget_info['has_budget'] is False
        assert budget_info['budget'] is None
    
    @pytest.mark.django_db
    def test_get_budget_info_safe_status(self):
        """Test get_budget_info with 'safe' status"""
        user = User.objects.create_user(username="testuser")
        budget = Budget.objects.create(
            user=user,
            monthly_limit=Decimal('1000.00'),
            warning_percentage=75,
            critical_percentage=90
        )
        
        current_amount = Decimal('500.00')  # 50% of limit
        budget_info = get_budget_info(user, current_amount)
        
        assert budget_info['has_budget'] is True
        assert budget_info['budget'] == budget
        assert budget_info['budget_status'] == 'safe'
        assert budget_info['budget_percentage_used'] == 50.0
        assert budget_info['budget_remaining'] == Decimal('500.00')
        assert '✅' in budget_info['budget_icon']
        assert 'text-green-600' in budget_info['budget_color_class']
        assert "You're doing well!" in budget_info['budget_message']
    
    @pytest.mark.django_db
    def test_get_budget_info_warning_status(self):
        """Test get_budget_info with 'warning' status"""
        user = User.objects.create_user(username="testuser")
        Budget.objects.create(
            user=user,
            monthly_limit=Decimal('1000.00'),
            warning_percentage=75,
            critical_percentage=90
        )
        
        current_amount = Decimal('800.00')  # 80% of limit
        budget_info = get_budget_info(user, current_amount)
        
        assert budget_info['budget_status'] == 'warning'
        assert budget_info['budget_percentage_used'] == 80.0
        assert budget_info['budget_remaining'] == Decimal('200.00')
        assert '⚠️' in budget_info['budget_icon']
        assert 'text-yellow-600' in budget_info['budget_color_class']
        assert 'Careful!' in budget_info['budget_message']
    
    @pytest.mark.django_db
    def test_get_budget_info_critical_status(self):
        """Test get_budget_info with 'critical' status"""
        user = User.objects.create_user(username="testuser")
        Budget.objects.create(
            user=user,
            monthly_limit=Decimal('1000.00'),
            warning_percentage=75,
            critical_percentage=90
        )
        
        current_amount = Decimal('950.00')  # 95% of limit
        budget_info = get_budget_info(user, current_amount)
        
        assert budget_info['budget_status'] == 'critical'
        assert budget_info['budget_percentage_used'] == 95.0
        assert budget_info['budget_remaining'] == Decimal('50.00')
        assert '🚨' in budget_info['budget_icon']
        assert 'text-red-600' in budget_info['budget_color_class']
        assert 'Limit almost reached!' in budget_info['budget_message']
    
    @pytest.mark.django_db
    def test_get_budget_info_exceeded_status(self):
        """Test get_budget_info with 'exceeded' status"""
        user = User.objects.create_user(username="testuser")
        Budget.objects.create(
            user=user,
            monthly_limit=Decimal('1000.00'),
            warning_percentage=75,
            critical_percentage=90
        )
        
        current_amount = Decimal('1200.00')  # 120% of limit
        budget_info = get_budget_info(user, current_amount)
        
        assert budget_info['budget_status'] == 'exceeded'
        assert budget_info['budget_percentage_used'] == 100.0  # Máximo 100%
        assert budget_info['budget_remaining'] == 0
        assert '🛑' in budget_info['budget_icon']
        assert 'text-red-600' in budget_info['budget_color_class']
        assert 'Limit exceeded!' in budget_info['budget_message']
        assert '₹200' in budget_info['budget_message']  # Excess amount included
    
    @pytest.mark.django_db
    def test_get_budget_info_custom_percentages(self):
        """Test get_budget_info with custom percentages"""
        user = User.objects.create_user(username="testuser")
        Budget.objects.create(
            user=user,
            monthly_limit=Decimal('2000.00'),
            warning_percentage=60,  # Personalizado
            critical_percentage=80  # Personalizado
        )
        
        # Test yellow alert with custom percentages
        current_amount = Decimal('1400.00')  # 70% of limit
        budget_info = get_budget_info(user, current_amount)
        
        assert budget_info['budget_status'] == 'warning'  # Between 60% and 80%
        assert budget_info['budget_percentage_used'] == 70.0


class TestExpenseListUtils:
    """Tests for expense list utilities"""
    
    def test_calculate_expense_statistics_empty(self):
        """Test statistics with empty QuerySet"""
        from django.db.models import QuerySet
        from apps.expenses.models import Expense
        
        empty_queryset = Expense.objects.none()
        stats = calculate_expense_statistics(empty_queryset)
        
        assert stats['total_filtered'] == 0
        assert stats['count_filtered'] == 0
    
    @pytest.mark.django_db
    def test_calculate_expense_statistics_with_data(self):
        """Test statistics with real data"""
        user = User.objects.create_user(username="testuser")
        category = Category.objects.create(name="Test", color="#FF0000")
        
        # Create expenses
        Expense.objects.create(
            user=user, category=category, amount=Decimal('15.00'), date=date.today()
        )
        Expense.objects.create(
            user=user, category=category, amount=Decimal('25.00'), date=date.today()
        )
        
        expenses = Expense.objects.filter(user=user)
        stats = calculate_expense_statistics(expenses)
        
        assert stats['total_filtered'] == Decimal('40.00')
        assert stats['count_filtered'] == 2
    
    def test_detect_active_filters_empty_form(self):
        """Test detection with empty form"""
        form = ExpenseFilterForm({})
        
        has_filters = detect_active_filters(form)
        assert has_filters is False
    
    def test_detect_active_filters_with_data(self):
        """Test detection with active filters"""
        form_data = {
            'period': 'current_month',
            'min_amount': '10.00'
        }
        form = ExpenseFilterForm(form_data)
        
        has_filters = detect_active_filters(form)
        assert has_filters is True


class TestCrudOperations:
    """Tests for CRUD operations"""
    
    @pytest.mark.django_db
    def test_get_expense_for_user_success(self):
        """Test get expense that belongs to the user"""
        user = User.objects.create_user(username="testuser")
        category = Category.objects.create(name="Test", color="#FF0000")
        
        expense = Expense.objects.create(
            user=user, category=category, amount=Decimal('15.00'), date=date.today()
        )
        
        retrieved_expense = get_expense_for_user(expense.id, user)
        assert retrieved_expense == expense
    
    @pytest.mark.django_db
    def test_get_expense_for_user_not_owner(self):
        """Test get expense that does NOT belong to the user"""
        user1 = User.objects.create_user(username="user1")
        user2 = User.objects.create_user(username="user2")
        category = Category.objects.create(name="Test", color="#FF0000")
        
        expense = Expense.objects.create(
            user=user1, category=category, amount=Decimal('15.00'), date=date.today()
        )
        
        with pytest.raises(Expense.DoesNotExist):
            get_expense_for_user(expense.id, user2)
    
    @pytest.mark.django_db
    def test_handle_expense_creation_valid(self):
        """Test successful expense creation"""
        user = User.objects.create_user(username="testuser")
        category = Category.objects.create(name="Test", color="#FF0000")
        
        form_data = {
            'category': category.id,
            'amount': '25.50',
            'description': 'Test expense',
            'date': date.today()
        }
        
        expense, form, is_valid = handle_expense_creation(form_data, user)
        
        assert is_valid is True
        assert expense is not None
        assert expense.user == user
        assert expense.amount == Decimal('25.50')
    
    @pytest.mark.django_db 
    def test_handle_expense_creation_invalid(self):
        """Test failed creation due to invalid data"""
        user = User.objects.create_user(username="testuser")
        
        form_data = {
            'amount': 'invalid_amount',  # Invalid
            'description': 'Test expense'
        }
        
        expense, form, is_valid = handle_expense_creation(form_data, user)
        
        assert is_valid is False
        assert expense is None
        assert form.errors  # Should have errors


# =============================================================================
# HOW TO RUN THESE TESTS
# =============================================================================
"""
To run the utilities tests, use these commands:

1. Run ALL tests in this file:
   pytest apps/expenses/tests/test_utils.py -v

2. Run only Dashboard tests:
   pytest apps/expenses/tests/test_utils.py::TestDashboardUtils -v

3. Run only Budget tests:
   pytest apps/expenses/tests/test_utils.py::TestBudgetUtils -v

4. Run only ExpenseList tests:
   pytest apps/expenses/tests/test_utils.py::TestExpenseListUtils -v

5. Run only CRUD Operations tests:
   pytest apps/expenses/tests/test_utils.py::TestCrudOperations -v

6. Run a specific test:
   pytest apps/expenses/tests/test_utils.py::TestBudgetUtils::test_get_budget_info_safe_status -v

7. Run only tests that use the database:
   pytest apps/expenses/tests/test_utils.py -m django_db -v

8. Run with coverage of utilities:
   pytest apps/expenses/tests/test_utils.py --cov=apps.expenses.utils -v

9. Run from the project root (faster):
   pytest -k "test_utils" -v

Tips:
- Use -v for verbose output (more details)
- Use -s to see debug prints
- Use --tb=short for shorter stack traces
- Use -x to stop at first failure

Full example with all options:
pytest apps/expenses/tests/test_utils.py -v -s --tb=short --cov=apps.expenses.utils
"""