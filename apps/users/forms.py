from django import forms
from django.contrib.auth.models import User
from apps.expenses.models import Budget


class UserProfileForm(forms.ModelForm):
    """
    Form to edit the user's profile
    Allows changing email, first and last name for n8n alert configuration
    """
    
    # Additional field for email alerts (from Budget model)
    email_alerts_enabled = forms.BooleanField(
        required=False,
        label="Email Alerts",
        help_text="Receive an email notification when exceeding the budget limit",
        widget=forms.CheckboxInput(attrs={
            'class': 'rounded border-gray-300 text-indigo-600 shadow-sm focus:border-indigo-500 focus:ring-indigo-500'
        })
    )
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'placeholder': 'Your first name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'placeholder': 'Your last name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'placeholder': 'tu@email.com',
                'required': True
            }),
        }
        labels = {
            'first_name': 'First name',
            'last_name': 'Last name',
            'email': 'Email',
        }
        help_texts = {
            'email': 'This email will be used for n8n alerts and automatic reports',
            'first_name': 'Optional - used to personalize reports',
            'last_name': 'Optional - used to personalize reports'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Initialize alerts field if the user has a budget
        if self.instance and hasattr(self.instance, 'budget'):
            self.fields['email_alerts_enabled'].initial = self.instance.budget.email_alerts_enabled
        else:
            # If no budget, hide the field
            del self.fields['email_alerts_enabled']
    
    def save(self, commit=True):
        """
        Save both the user and the budget alert configuration
        """
        user = super().save(commit=commit)
        
        # If alerts field exists and user has a budget
        if 'email_alerts_enabled' in self.cleaned_data and hasattr(user, 'budget'):
            user.budget.email_alerts_enabled = self.cleaned_data['email_alerts_enabled']
            if commit:
                user.budget.save()
        
        return user
    
    def clean_email(self):
        """
        Custom validation for the email
        """
        email = self.cleaned_data.get('email')
        if email:
            # Ensure no other user has this email (except the current one)
            existing_user = User.objects.filter(email=email).exclude(pk=self.instance.pk)
            if existing_user.exists():
                raise forms.ValidationError('Another user with this email already exists.')
        return email 