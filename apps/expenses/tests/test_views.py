"""
Tests for expenses views

Covers dashboard, expense CRUD, HTMX, and authentication features
"""
import pytest
from datetime import date, timedelta
from decimal import Decimal
from django.test import Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from apps.expenses.models import Category, Expense


@pytest.mark.django_db
class TestDashboardView:
    """Tests for the dashboard view"""
    
    def setup_method(self):
        """Initial setup for each test"""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123"
        )
        self.category = Category.objects.create(
            name="Test Category",
            color="#FF0000"
        )
    
    def test_dashboard_requires_login(self):
        """Test that dashboard requires authentication"""
        response = self.client.get(reverse('expenses:dashboard'))
        assert response.status_code == 302  # Redirect a login
        assert '/admin/login/' in response.url or '/login/' in response.url
    
    def test_dashboard_get_authenticated(self):
        """Test GET dashboard with authenticated user"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse('expenses:dashboard'))
        
        assert response.status_code == 200
        assert 'expenses/dashboard.html' in [t.name for t in response.templates]
        assert 'period_total' in response.context
        assert 'period_label' in response.context
    
    def test_dashboard_htmx_request(self):
        """Test dashboard with HTMX request"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(
            reverse('expenses:dashboard'),
            HTTP_HX_REQUEST='true'
        )
        
        assert response.status_code == 200
        assert 'expenses/partials/dashboard_metrics.html' in [t.name for t in response.templates]
    
    def test_dashboard_with_period_filter(self):
        """Test dashboard with period filter"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(
            reverse('expenses:dashboard'),
            {'period': 'last_7_days'}
        )
        
        assert response.status_code == 200
        assert response.context['period_label'] == "Últimos 7 días"
    
    def test_dashboard_with_expenses_data(self):
        """Test dashboard with expenses data"""
        self.client.login(username="testuser", password="testpass123")
        
        # Crear algunos gastos
        Expense.objects.create(
            user=self.user,
            category=self.category,
            amount=Decimal('25.00'),
            description="Test expense",
            date=date.today()
        )
        
        response = self.client.get(reverse('expenses:dashboard'))
        
        assert response.status_code == 200
        assert response.context['period_total'] == Decimal('25.00')
        assert response.context['period_expenses_count'] == 1


@pytest.mark.django_db
class TestExpenseListView:
    """Tests for the expense list view"""
    
    def setup_method(self):
        """Initial setup for each test"""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123"
        )
        self.category = Category.objects.create(
            name="Test Category",
            color="#FF0000"
        )
    
    def test_expense_list_requires_login(self):
        """Test that expense_list requires authentication"""
        response = self.client.get(reverse('expenses:expense_list'))
        assert response.status_code == 302  # Redirect a login
    
    def test_expense_list_get_authenticated(self):
        """Test GET expense_list with authenticated user"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse('expenses:expense_list'))
        
        assert response.status_code == 200
        assert 'expenses/expense_list.html' in [t.name for t in response.templates]
        assert 'expenses' in response.context
        assert 'filter_form' in response.context
    
    def test_expense_list_htmx_request(self):
        """Test expense_list with HTMX request"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(
            reverse('expenses:expense_list'),
            HTTP_HX_REQUEST='true'
        )
        
        assert response.status_code == 200
        assert 'expenses/partials/expense_list_content.html' in [t.name for t in response.templates]
    
    def test_expense_list_with_filters(self):
        """Test expense_list with applied filters"""
        self.client.login(username="testuser", password="testpass123")
        
        # Crear gastos con diferentes categorías
        other_category = Category.objects.create(name="Other", color="#00FF00")
        Expense.objects.create(
            user=self.user, category=self.category,
            amount=Decimal('10.00'), date=date.today()
        )
        Expense.objects.create(
            user=self.user, category=other_category,
            amount=Decimal('20.00'), date=date.today()
        )
        
        # Filtrar por categoría
        response = self.client.get(
            reverse('expenses:expense_list'),
            {'category': self.category.id}
        )
        
        assert response.status_code == 200
        # Verificar que solo aparezca el gasto de la categoría filtrada
        expenses = list(response.context['expenses'])
        assert len(expenses) == 1
        assert expenses[0].category == self.category


@pytest.mark.django_db
class TestAddExpenseView:
    """Tests for the add expense view"""
    
    def setup_method(self):
        """Initial setup for each test"""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123"
        )
        self.category = Category.objects.create(
            name="Test Category",
            color="#FF0000"
        )
    
    def test_add_expense_requires_login(self):
        """Test that add_expense requires authentication"""
        response = self.client.get(reverse('expenses:add_expense'))
        assert response.status_code == 302  # Redirect a login
    
    def test_add_expense_get_authenticated(self):
        """Test GET add_expense with authenticated user"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse('expenses:add_expense'))
        
        assert response.status_code == 200
        assert 'expenses/add_expense.html' in [t.name for t in response.templates]
        assert 'form' in response.context
        # La vista no devuelve categories directamente, sino que el form las contiene
    
    def test_add_expense_htmx_get(self):
        """Test GET add_expense with HTMX request (modal)"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(
            reverse('expenses:add_expense'),
            HTTP_HX_REQUEST='true'
        )
        
        assert response.status_code == 200
        assert 'expenses/partials/add_expense_modal.html' in [t.name for t in response.templates]
    
    def test_add_expense_post_valid_data(self):
        """Test POST add_expense with valid data"""
        self.client.login(username="testuser", password="testpass123")
        
        form_data = {
            'category': self.category.id,
            'amount': '25.50',
            'description': 'Test expense',
            'date': date.today().strftime('%Y-%m-%d')
        }
        
        response = self.client.post(reverse('expenses:add_expense'), form_data)
        
        # Verificar redirect exitoso
        assert response.status_code == 302
        assert response.url == reverse('expenses:dashboard')
        
        # Verificar que el gasto se creó
        expense = Expense.objects.get(user=self.user)
        assert expense.amount == Decimal('25.50')
        assert expense.description == 'Test expense'
        assert expense.category == self.category
        
        # Verificar mensaje de éxito
        messages = list(get_messages(response.wsgi_request))
        assert any('exitosamente' in str(message) for message in messages)
    
    def test_add_expense_post_htmx_valid(self):
        """Test POST add_expense with HTMX and valid data"""
        self.client.login(username="testuser", password="testpass123")
        
        form_data = {
            'category': self.category.id,
            'amount': '15.00',
            'description': 'HTMX expense',
            'date': date.today().strftime('%Y-%m-%d')
        }
        
        response = self.client.post(
            reverse('expenses:add_expense'),
            form_data,
            HTTP_HX_REQUEST='true'
        )
        
        assert response.status_code == 200
        assert 'expenses/partials/expense_success.html' in [t.name for t in response.templates]
        
        # Verificar que el gasto se creó
        expense = Expense.objects.get(user=self.user)
        assert expense.amount == Decimal('15.00')
    
    def test_add_expense_post_invalid_data(self):
        """Test POST add_expense with invalid data"""
        self.client.login(username="testuser", password="testpass123")
        
        form_data = {
            'category': '',  # Categoría vacía (inválida)
            'amount': 'invalid',  # Amount inválido
            'description': 'Test expense',
            'date': 'invalid-date'
        }
        
        response = self.client.post(
            reverse('expenses:add_expense'),
            form_data,
            HTTP_HX_REQUEST='true'
        )
        
        assert response.status_code == 200
        assert 'expenses/partials/add_expense_modal.html' in [t.name for t in response.templates]
        assert 'form' in response.context
        assert response.context['form'].errors
        
        # Verificar que NO se creó ningún gasto
        assert Expense.objects.count() == 0


@pytest.mark.django_db
class TestEditExpenseView:
    """Tests for the edit expense view"""
    
    def setup_method(self):
        """Initial setup for each test"""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123"
        )
        self.other_user = User.objects.create_user(
            username="otheruser",
            password="otherpass123"
        )
        self.category = Category.objects.create(
            name="Test Category",
            color="#FF0000"
        )
        self.expense = Expense.objects.create(
            user=self.user,
            category=self.category,
            amount=Decimal('20.00'),
            description="Original expense",
            date=date.today()
        )
    
    def test_edit_expense_requires_login(self):
        """Test that edit_expense requires authentication"""
        response = self.client.get(
            reverse('expenses:edit_expense', kwargs={'expense_id': self.expense.id})
        )
        assert response.status_code == 302  # Redirect a login
    
    def test_edit_expense_get_owner(self):
        """Test GET edit_expense as expense owner (HTMX only)"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(
            reverse('expenses:edit_expense', kwargs={'expense_id': self.expense.id}),
            HTTP_HX_REQUEST='true'  # La vista solo maneja HTMX
        )
        
        assert response.status_code == 200
        assert 'expenses/partials/edit_expense_modal.html' in [t.name for t in response.templates]
        assert 'form' in response.context
        assert 'expense' in response.context
        assert response.context['expense'] == self.expense
    
    def test_edit_expense_get_not_owner(self):
        """Test GET edit_expense as NOT the expense owner"""
        self.client.login(username="otheruser", password="otherpass123")
        response = self.client.get(
            reverse('expenses:edit_expense', kwargs={'expense_id': self.expense.id})
        )
        
        # Debería devolver error o redirect
        assert response.status_code == 404 or response.status_code == 302
    
    def test_edit_expense_htmx_get(self):
        """Test GET edit_expense with HTMX request (modal)"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(
            reverse('expenses:edit_expense', kwargs={'expense_id': self.expense.id}),
            HTTP_HX_REQUEST='true'
        )
        
        assert response.status_code == 200
        assert 'expenses/partials/edit_expense_modal.html' in [t.name for t in response.templates]
    
    def test_edit_expense_post_valid_data(self):
        """Test POST edit_expense with valid data"""
        self.client.login(username="testuser", password="testpass123")
        
        form_data = {
            'category': self.category.id,
            'amount': '35.00',  # Cambiar amount
            'description': 'Updated expense',  # Cambiar descripción
            'date': date.today().strftime('%Y-%m-%d')
        }
        
        response = self.client.post(
            reverse('expenses:edit_expense', kwargs={'expense_id': self.expense.id}),
            form_data
        )
        
        # Verificar redirect exitoso
        assert response.status_code == 302
        assert response.url == reverse('expenses:expense_list')
        
        # Verificar que el gasto se actualizó
        self.expense.refresh_from_db()
        assert self.expense.amount == Decimal('35.00')
        assert self.expense.description == 'Updated expense'
        
        # Verificar mensaje de éxito
        messages = list(get_messages(response.wsgi_request))
        assert any('actualizado exitosamente' in str(message) for message in messages)
    
    def test_edit_expense_nonexistent(self):
        """Test edit_expense con ID de gasto inexistente"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(
            reverse('expenses:edit_expense', kwargs={'expense_id': 99999})
        )
        
        # Debería manejar el error adecuadamente
        assert response.status_code == 404 or response.status_code == 302


@pytest.mark.django_db
class TestDeleteExpenseView:
    """Tests for the delete expense view"""
    
    def setup_method(self):
        """Configuración inicial para cada test"""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123"
        )
        self.other_user = User.objects.create_user(
            username="otheruser",
            password="otherpass123"
        )
        self.category = Category.objects.create(
            name="Test Category",
            color="#FF0000"
        )
        self.expense = Expense.objects.create(
            user=self.user,
            category=self.category,
            amount=Decimal('20.00'),
            description="To be deleted",
            date=date.today()
        )
    
    def test_delete_expense_requires_login(self):
        """Test que delete_expense requiere autenticación"""
        response = self.client.delete(
            reverse('expenses:delete_expense', kwargs={'expense_id': self.expense.id})
        )
        assert response.status_code == 302  # Redirect a login
    
    def test_delete_expense_owner_success(self):
        """Test DELETE expense como propietario"""
        self.client.login(username="testuser", password="testpass123")
        
        # Verificar que el gasto existe antes
        assert Expense.objects.filter(id=self.expense.id).exists()
        
        response = self.client.delete(
            reverse('expenses:delete_expense', kwargs={'expense_id': self.expense.id})
        )
        
        # Verificar redirect exitoso
        assert response.status_code == 302
        assert response.url == reverse('expenses:expense_list')
        
        # Verificar que el gasto se eliminó
        assert not Expense.objects.filter(id=self.expense.id).exists()
        
        # Verificar mensaje de éxito
        messages = list(get_messages(response.wsgi_request))
        assert any('eliminado exitosamente' in str(message) for message in messages)
    
    def test_delete_expense_not_owner(self):
        """Test DELETE expense como NO propietario"""
        self.client.login(username="otheruser", password="otherpass123")
        
        response = self.client.delete(
            reverse('expenses:delete_expense', kwargs={'expense_id': self.expense.id})
        )
        
        # Debería manejar el error
        assert response.status_code in [404, 403, 302]
        
        # Verificar que el gasto NO se eliminó
        assert Expense.objects.filter(id=self.expense.id).exists()
    
    def test_delete_expense_htmx_success(self):
        """Test DELETE expense con petición HTMX"""
        self.client.login(username="testuser", password="testpass123")
        
        response = self.client.delete(
            reverse('expenses:delete_expense', kwargs={'expense_id': self.expense.id}),
            HTTP_HX_REQUEST='true'
        )
        
        assert response.status_code == 200
        # La respuesta HTMX devuelve la lista actualizada, no un template específico de success
        assert 'expenses/partials/expense_list_content.html' in [t.name for t in response.templates]
        
        # Verificar que el gasto se eliminó
        assert not Expense.objects.filter(id=self.expense.id).exists()
    
    def test_delete_expense_nonexistent(self):
        """Test DELETE expense con ID inexistente"""
        self.client.login(username="testuser", password="testpass123")
        
        response = self.client.delete(
            reverse('expenses:delete_expense', kwargs={'expense_id': 99999})
        )
        
        # Debería manejar el error adecuadamente
        assert response.status_code in [404, 302]


@pytest.mark.django_db
class TestCloseModalView:
    """Tests for the close_modal view"""
    
    def setup_method(self):
        """Configuración inicial para cada test"""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123"
        )
    
    def test_close_modal_requires_login(self):
        """Test que close_modal requiere autenticación"""
        response = self.client.get(reverse('expenses:close_modal'))
        assert response.status_code == 302  # Redirect a login
    
    def test_close_modal_authenticated(self):
        """Test close_modal con usuario autenticado"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse('expenses:close_modal'))
        
        assert response.status_code == 200
        assert 'expenses/partials/empty.html' in [t.name for t in response.templates]


# =============================================================================
# HOW TO RUN THESE TESTS
# =============================================================================
"""
To run the view tests, use these commands:

1. Run ALL tests in this file:
    pytest --ds=config.settings apps/expenses/tests/test_views.py -v

2. Run tests by specific view:
    pytest --ds=config.settings apps/expenses/tests/test_views.py::TestDashboardView -v
    pytest --ds=config.settings apps/expenses/tests/test_views.py::TestExpenseListView -v
    pytest --ds=config.settings apps/expenses/tests/test_views.py::TestAddExpenseView -v
    pytest --ds=config.settings apps/expenses/tests/test_views.py::TestEditExpenseView -v
    pytest --ds=config.settings apps/expenses/tests/test_views.py::TestDeleteExpenseView -v

3. Run a specific test:
    pytest --ds=config.settings apps/expenses/tests/test_views.py::TestDashboardView::test_dashboard_get_authenticated -v

4. Run tests with view coverage:
    pytest --ds=config.settings apps/expenses/tests/test_views.py --cov=apps.expenses.views -v

5. Run tests that require authentication:
    pytest --ds=config.settings apps/expenses/tests/test_views.py -k "authenticated" -v

6. Run only HTMX tests:
    pytest --ds=config.settings apps/expenses/tests/test_views.py -k "htmx" -v

7. Run from the project root:
    pytest --ds=config.settings -k "test_views" -v

8. Run with detailed output for debugging:
    pytest --ds=config.settings apps/expenses/tests/test_views.py -v -s --tb=long

Tips for view tests:
- Tests check status codes, used templates, and context
- Both normal and HTMX requests are tested
- Authentication and user permissions are validated
- Success and error cases are tested
- Redirects and messages are checked
- Data creation/editing/deletion is validated

Tests cover:
✓ Authentication (login_required)
✓ Permissions (expense ownership)
✓ HTTP responses (status codes)
✓ Rendered templates
✓ Template context
✓ HTMX functionality
✓ CRUD operations
✓ Form validation
✓ Success/error messages
✓ Proper redirects
"""