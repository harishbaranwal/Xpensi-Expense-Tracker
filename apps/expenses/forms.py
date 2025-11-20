from django import forms
from .models import Expense, Category, Budget
from datetime import datetime, date, timedelta


class DateInput(forms.DateInput):
    """
    Custom date widget that works correctly with HTML5
    """
    input_type = 'date'
    
    def format_value(self, value):
        if value is None:
            return ''
        if isinstance(value, str):
            return value
        return value.strftime('%Y-%m-%d') if value else ''


class ExpenseForm(forms.ModelForm):
    """
    Form to create and edit expenses
    """
    
    class Meta:
        model = Expense
        fields = ['category', 'amount', 'description', 'date', 'location']
        widgets = {
            'category': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'description': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'placeholder': 'Expense description (optional)'
            }),
            'date': DateInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500'
            }),
            'location': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'placeholder': 'Location (optional)'
            }),
        }
        labels = {
            'category': 'Category',
            'amount': 'Amount (₹)',
            'description': 'Description',
            'date': 'Date',
            'location': 'Location',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set today's date by default
        if not self.instance.pk:
            self.fields['date'].initial = date.today()
        
        # Order categories by name
        self.fields['category'].queryset = Category.objects.all().order_by('name') 


class ExpenseFilterForm(forms.Form):
    """
    Form to filter expenses by category, date and amount with quick filters
    """
    
    # Quick filter options by month/period
    MONTH_CHOICES = [
        ('', 'Select period'),
        ('current_month', 'This month'),
        ('last_month', 'Last month'),
        ('current_year', 'This year'),
        ('last_3_months', 'Last 3 months'),
        ('last_6_months', 'Last 6 months'),
        ('custom', 'Custom range'),
    ]
    
    # Quick period filter
    period = forms.ChoiceField(
        choices=MONTH_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500'
        }),
        label="Period"
    )
    
    # Category filter
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        empty_label="All categories",
        widget=forms.Select(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500'
        }),
        label="Category"
    )
    
    # From date filter
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
            'type': 'date'
        }),
        label="From"
    )
    
    # To date filter
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
            'type': 'date'
        }),
        label="To"
    )
    
    # Minimum amount filter
    min_amount = forms.DecimalField(
        required=False,
        min_value=0,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
            'step': '0.01',
            'min': '0',
            'placeholder': '0.00'
        }),
        label="Minimum amount (₹)"
    )
    
    # Maximum amount filter
    max_amount = forms.DecimalField(
        required=False,
        min_value=0,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
            'step': '0.01',
            'min': '0',
            'placeholder': '0.00'
        }),
        label="Maximum amount (₹)"
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Order categories by name
        self.fields['category'].queryset = Category.objects.all().order_by('name')
        
    def clean(self):
        """
        Custom validation to ensure filter consistency
        """
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        min_amount = cleaned_data.get('min_amount')
        max_amount = cleaned_data.get('max_amount')
        period = cleaned_data.get('period')
        
        # If a predefined period is selected, compute dates
        if period and period != 'custom':
            today = date.today()
            
            if period == 'current_month':
                date_from = today.replace(day=1)
                date_to = today
            elif period == 'last_month':
                if today.month == 1:
                    date_from = date(today.year - 1, 12, 1)
                    date_to = date(today.year - 1, 12, 31)
                else:
                    date_from = date(today.year, today.month - 1, 1)
                    # Last day of previous month
                    next_month = date(today.year, today.month, 1)
                    date_to = next_month - timedelta(days=1)
            elif period == 'current_year':
                date_from = date(today.year, 1, 1)
                date_to = today
            elif period == 'last_3_months':
                date_from = today - timedelta(days=90)
                date_to = today
            elif period == 'last_6_months':
                date_from = today - timedelta(days=180)
                date_to = today
            
            # Update calculated fields
            cleaned_data['date_from'] = date_from
            cleaned_data['date_to'] = date_to
        
        # Validate that from_date is not greater than to_date
        if date_from and date_to and date_from > date_to:
            raise forms.ValidationError("The 'from' date cannot be greater than the 'to' date.")
        
        # Validate that min_amount is not greater than max_amount
        if min_amount and max_amount and min_amount > max_amount:
            raise forms.ValidationError("The minimum amount cannot be greater than the maximum amount.")
        
        return cleaned_data


class BudgetForm(forms.ModelForm):
    """
    Form to configure the user's monthly budget
    """
    
    class Meta:
        model = Budget
        fields = ['monthly_limit', 'warning_percentage', 'critical_percentage', 'email_alerts_enabled']
        widgets = {
            'monthly_limit': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'step': '0.01',
                'min': '0',
                'placeholder': '500.00'
            }),
            'warning_percentage': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'min': '1',
                'max': '100',
                'placeholder': '75'
            }),
            'critical_percentage': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'min': '1',
                'max': '100',
                'placeholder': '90'
            }),
        }
        labels = {
            'monthly_limit': 'Monthly Limit (₹)',
            'warning_percentage': 'Yellow Alert (%)',
            'critical_percentage': 'Red Alert (%)',
        }
        help_texts = {
            'monthly_limit': 'Set your maximum monthly spending limit',
            'warning_percentage': 'Percentage of the limit to show yellow alert (recommended: 75%)',
            'critical_percentage': 'Percentage of the limit to show red alert (recommended: 90%)',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Smart defaults
        if not self.instance.pk:
            self.fields['warning_percentage'].initial = 75
            self.fields['critical_percentage'].initial = 90
    
    def clean(self):
        """
        Custom validation for the budget form
        """
        cleaned_data = super().clean()
        monthly_limit = cleaned_data.get('monthly_limit')
        warning_percentage = cleaned_data.get('warning_percentage')
        critical_percentage = cleaned_data.get('critical_percentage')
        
        # Validate that monthly limit is positive
        if monthly_limit and monthly_limit <= 0:
            raise forms.ValidationError({
                'monthly_limit': 'Monthly limit must be greater than zero.'
            })
        
        # Validate that warning_percentage < critical_percentage
        if warning_percentage and critical_percentage:
            if warning_percentage >= critical_percentage:
                raise forms.ValidationError({
                    'warning_percentage': 'Warning percentage must be less than the critical percentage.'
                })
        
        # Validate percentage ranges
        if warning_percentage and (warning_percentage < 1 or warning_percentage > 100):
            raise forms.ValidationError({
                'warning_percentage': 'Percentage must be between 1 and 100.'
            })
        
        if critical_percentage and (critical_percentage < 1 or critical_percentage > 100):
            raise forms.ValidationError({
                'critical_percentage': 'Percentage must be between 1 and 100.'
            })
        
        return cleaned_data 