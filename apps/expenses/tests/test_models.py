"""
Tests for expense models

Covers basic functionality of Category and Expense
"""
import pytest
from datetime import date, timedelta
from decimal import Decimal
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from apps.expenses.models import Category, Expense, Budget


@pytest.mark.django_db
class TestCategoryModel:
    """Tests for the Category model"""
    
    def test_create_category(self):
        """Basic test for creating a category"""
        category = Category.objects.create(
            name="Test Category",
            color="#FF0000"
        )
        assert category.name == "Test Category"
        assert category.color == "#FF0000"
        assert str(category) == "Test Category"
    
    def test_category_str_representation(self):
        """Test the Category __str__ method"""
        category = Category(name="Coffee")
        assert str(category) == "Coffee"
    
    def test_category_unique_name(self):
        """Test that category name is unique"""
        Category.objects.create(name="Coffee", color="#8B4513")
        
        with pytest.raises(Exception):  # IntegrityError for unique constraint
            Category.objects.create(name="Coffee", color="#FF0000")


@pytest.mark.django_db
class TestExpenseModel:
    """Tests for the Expense model"""
    
    def test_create_expense(self):
        """Basic test for creating an expense"""
        # Create user and category
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        category = Category.objects.create(
            name="Test Category",
            color="#FF0000"
        )
        
        # Create expense
        expense = Expense.objects.create(
            user=user,
            category=category,
            amount=Decimal('15.50'),
            description="Test expense",
            date=date.today()
        )
        
        assert expense.user == user
        assert expense.category == category
        assert expense.amount == Decimal('15.50')
        assert expense.description == "Test expense"
        assert expense.date == date.today()
    
    def test_expense_str_representation(self):
        """Test the Expense __str__ method"""
        user = User.objects.create_user(username="testuser")
        category = Category.objects.create(name="Coffee", color="#8B4513")
        
        expense_date = date.today()
        expense = Expense.objects.create(
            user=user,
            category=category,
            amount=Decimal('5.00'),
            description="Morning coffee",
            date=expense_date
        )
        
        expected_str = f"{expense.amount}₹ - Coffee ({expense_date})"
        assert str(expense) == expected_str
    
    def test_expense_without_description(self):
        """Test expense without description"""
        user = User.objects.create_user(username="testuser")
        category = Category.objects.create(name="Coffee", color="#8B4513")
        
        expense = Expense.objects.create(
            user=user,
            category=category,
            amount=Decimal('5.00'),
            date=date.today()
            # Without description
        )
        
        assert expense.description is None or expense.description == ""
    
    def test_expense_amount_validation(self):
        """Test validation of positive amount"""
        user = User.objects.create_user(username="testuser")
        category = Category.objects.create(name="Test", color="#FF0000")
        
        # Amount must be positive
        expense = Expense(
            user=user,
            category=category,
            amount=Decimal('-5.00'),  # Negativo
            description="Test",
            date=date.today()
        )
        
        with pytest.raises(ValidationError):
            expense.full_clean()
    
    def test_expense_ordering(self):
        """Test default ordering of expenses"""
        user = User.objects.create_user(username="testuser")
        category = Category.objects.create(name="Test", color="#FF0000")
        
        # Create multiple expenses with different dates
        today = date.today()
        yesterday = today - timedelta(days=1)
        two_days_ago = today - timedelta(days=2)
        
        expense1 = Expense.objects.create(
            user=user, category=category, amount=Decimal('10.00'), date=two_days_ago
        )
        expense2 = Expense.objects.create(
            user=user, category=category, amount=Decimal('20.00'), date=yesterday
        )
        expense3 = Expense.objects.create(
            user=user, category=category, amount=Decimal('30.00'), date=today
        )
        
        # Verify ordering (most recent first by default in Meta)
        expenses = list(Expense.objects.all())
        assert expenses[0] == expense3  # Más reciente (hoy)
        assert expenses[1] == expense2  # Ayer
        assert expenses[2] == expense1  # Hace dos días


# =============================================================================
# HOW TO RUN THESE TESTS
# =============================================================================
"""
To run the model tests, use these commands:

1. Run ALL tests in this file:
   pytest apps/expenses/tests/test_models.py -v

2. Run only Category tests:
   pytest apps/expenses/tests/test_models.py::TestCategoryModel -v

3. Run only Expense tests:
   pytest apps/expenses/tests/test_models.py::TestExpenseModel -v

4. Run only Budget tests:
   pytest apps/expenses/tests/test_models.py::TestBudgetModel -v

5. Run a specific test:
   pytest apps/expenses/tests/test_models.py::TestBudgetModel::test_create_budget -v

6. Run with code coverage:
   pytest apps/expenses/tests/test_models.py --cov=apps.expenses.models -v

7. Run from the project root (faster):
   pytest -k "test_models" -v
"""


@pytest.mark.django_db
class TestBudgetModel:
    """Tests for the Budget model"""
    
    def test_create_budget(self):
        """Basic test for creating a budget"""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        
        budget = Budget.objects.create(
            user=user,
            monthly_limit=Decimal('500.00'),
            warning_percentage=75,
            critical_percentage=90
        )
        
        assert budget.user == user
        assert budget.monthly_limit == Decimal('500.00')
        assert budget.warning_percentage == 75
        assert budget.critical_percentage == 90
    
    def test_budget_str_representation(self):
        """Test the Budget __str__ method"""
        user = User.objects.create_user(username="testuser")
        budget = Budget.objects.create(
            user=user,
            monthly_limit=Decimal('1000.00')
        )
        
        expected_str = f"Budget of testuser: ₹1000.00/month"
        assert str(budget) == expected_str
    
    def test_budget_one_to_one_constraint(self):
        """Test that each user can only have one budget"""
        user = User.objects.create_user(username="testuser")
        
        # Crear primer presupuesto
        Budget.objects.create(
            user=user,
            monthly_limit=Decimal('500.00')
        )
        
        # Intentar crear segundo presupuesto para el mismo usuario
        with pytest.raises(Exception):  # IntegrityError for OneToOneField
            Budget.objects.create(
                user=user,
                monthly_limit=Decimal('1000.00')
            )
    
    def test_budget_validation_positive_limit(self):
        """Test validation of positive limit"""
        user = User.objects.create_user(username="testuser")
        
        budget = Budget(
            user=user,
            monthly_limit=Decimal('-100.00'),  # Negative
            warning_percentage=75,
            critical_percentage=90
        )
        
        with pytest.raises(ValidationError):
            budget.full_clean()
    
    def test_budget_validation_percentage_order(self):
        """Test validation that warning < critical"""
        user = User.objects.create_user(username="testuser")
        
        budget = Budget(
            user=user,
            monthly_limit=Decimal('500.00'),
            warning_percentage=95,  # Greater than critical
            critical_percentage=90
        )
        
        with pytest.raises(ValidationError):
            budget.full_clean()
    
    def test_get_warning_amount(self):
        """Test calculation of yellow alert amount"""
        user = User.objects.create_user(username="testuser")
        budget = Budget.objects.create(
            user=user,
            monthly_limit=Decimal('1000.00'),
            warning_percentage=75
        )
        
        warning_amount = budget.get_warning_amount()
        assert warning_amount == Decimal('750.00')  # 75% of 1000
    
    def test_get_critical_amount(self):
        """Test calculation of red alert amount"""
        user = User.objects.create_user(username="testuser")
        budget = Budget.objects.create(
            user=user,
            monthly_limit=Decimal('1000.00'),
            critical_percentage=90
        )
        
        critical_amount = budget.get_critical_amount()
        assert critical_amount == Decimal('900.00')  # 90% of 1000
    
    def test_get_percentage_used_normal(self):
        """Test percentage used - normal case"""
        user = User.objects.create_user(username="testuser")
        budget = Budget.objects.create(
            user=user,
            monthly_limit=Decimal('1000.00')
        )
        
        percentage = budget.get_percentage_used(Decimal('250.00'))
        assert percentage == 25.0  # 250/1000 * 100
    
    def test_get_percentage_used_over_limit(self):
        """Test percentage used - over the limit"""
        user = User.objects.create_user(username="testuser")
        budget = Budget.objects.create(
            user=user,
            monthly_limit=Decimal('1000.00')
        )
        
        percentage = budget.get_percentage_used(Decimal('1500.00'))
        assert percentage == 100.0  # Max 100% even if more
    
    def test_get_percentage_used_zero_limit(self):
        """Test percentage calculation with zero limit"""
        user = User.objects.create_user(username="testuser")
        budget = Budget.objects.create(
            user=user,
            monthly_limit=Decimal('0.00')
        )
        
        percentage = budget.get_percentage_used(Decimal('100.00'))
        assert percentage == 0  # Division by zero protection
    
    def test_get_remaining_amount_positive(self):
        """Test remaining amount - positive case"""
        user = User.objects.create_user(username="testuser")
        budget = Budget.objects.create(
            user=user,
            monthly_limit=Decimal('1000.00')
        )
        
        remaining = budget.get_remaining_amount(Decimal('300.00'))
        assert remaining == Decimal('700.00')  # 1000 - 300
    
    def test_get_remaining_amount_exceeded(self):
        """Test remaining amount - limit exceeded"""
        user = User.objects.create_user(username="testuser")
        budget = Budget.objects.create(
            user=user,
            monthly_limit=Decimal('1000.00')
        )
        
        remaining = budget.get_remaining_amount(Decimal('1200.00'))
        assert remaining == 0  # Never negative
    
    def test_get_status_for_amount_safe(self):
        """Test status 'safe' - low spending"""
        user = User.objects.create_user(username="testuser")
        budget = Budget.objects.create(
            user=user,
            monthly_limit=Decimal('1000.00'),
            warning_percentage=75,
            critical_percentage=90
        )
        
        status = budget.get_status_for_amount(Decimal('500.00'))  # 50%
        assert status == 'safe'
    
    def test_get_status_for_amount_warning(self):
        """Test status 'warning' - yellow alert"""
        user = User.objects.create_user(username="testuser")
        budget = Budget.objects.create(
            user=user,
            monthly_limit=Decimal('1000.00'),
            warning_percentage=75,
            critical_percentage=90
        )
        
        status = budget.get_status_for_amount(Decimal('800.00'))  # 80%
        assert status == 'warning'
    
    def test_get_status_for_amount_critical(self):
        """Test status 'critical' - red alert"""
        user = User.objects.create_user(username="testuser")
        budget = Budget.objects.create(
            user=user,
            monthly_limit=Decimal('1000.00'),
            warning_percentage=75,
            critical_percentage=90
        )
        
        status = budget.get_status_for_amount(Decimal('950.00'))  # 95%
        assert status == 'critical'
    
    def test_get_status_for_amount_exceeded(self):
        """Test status 'exceeded' - limit surpassed"""
        user = User.objects.create_user(username="testuser")
        budget = Budget.objects.create(
            user=user,
            monthly_limit=Decimal('1000.00'),
            warning_percentage=75,
            critical_percentage=90
        )
        
        status = budget.get_status_for_amount(Decimal('1100.00'))  # 110%
        assert status == 'exceeded' 