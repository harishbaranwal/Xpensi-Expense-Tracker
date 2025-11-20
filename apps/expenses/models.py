from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class Category(models.Model):
    """Expense categories: coffee, delivery, transport, etc."""
    
    name = models.CharField(max_length=100, unique=True, verbose_name="Name")
    icon = models.CharField(max_length=50, verbose_name="Icon")
    color = models.CharField(max_length=7, verbose_name="Color")  # Hex color
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    
    # Auditing fields
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created at")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated at")

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ['name']

    def __str__(self):
        return self.name


class Expense(models.Model):
    """Single expense recorded by the user"""
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,  # Deleting the user deletes their expenses
        verbose_name="User",
        related_name="expenses"
    )
    
    category = models.ForeignKey(
        Category, 
        on_delete=models.PROTECT,  # Cannot delete category with existing expenses
        verbose_name="Category",
        related_name="expenses"
    )
    
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,  # Prefer DecimalField over FloatField for money
        verbose_name="Amount"
    )
    
    description = models.CharField(
        max_length=255, 
        blank=True, 
        null=True, 
        verbose_name="Description"
    )
    
    date = models.DateField(verbose_name="Date")
    location = models.CharField(
        max_length=200, 
        blank=True, 
        null=True, 
        verbose_name="Location"
    )
    
    # Auditing fields
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created at")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated at")

    class Meta:
        verbose_name = "Expense"
        verbose_name_plural = "Expenses"
        ordering = ['-date', '-created_at']  # Newest first

    def clean(self):
        """Custom model validations"""
        super().clean()
        if self.amount and self.amount <= 0:
            raise ValidationError({
                'amount': 'Amount must be greater than zero.'
            })

    def __str__(self):
        return f"{self.amount}₹ - {self.category.name} ({self.date})"


class Budget(models.Model):
    """User budget limit to control spending"""
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        verbose_name="User",
        related_name="budget"
    )
    
    monthly_limit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Monthly Limit",
        help_text="Maximum spending per month in euros"
    )
    
    # Alert configuration
    warning_percentage = models.PositiveIntegerField(
        default=75,
        verbose_name="Warning Percentage",
        help_text="Percentage of the limit to show yellow alert (e.g., 75)",
        error_messages={
            'invalid': 'Invalid percentage value.'
        }
    )
    
    critical_percentage = models.PositiveIntegerField(
        default=90,
        verbose_name="Critical Percentage",
        help_text="Percentage of the limit to show red alert (e.g., 90)"
    )
    
    # Email notification configuration
    email_alerts_enabled = models.BooleanField(
        default=False,
        verbose_name="Email Alerts",
        help_text="Receive email when the critical percentage is exceeded"
    )
    
    # Auditing fields
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created at")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated at")
    
    class Meta:
        verbose_name = "Budget"
        verbose_name_plural = "Budgets"
    
    def clean(self):
        """Custom model validations"""
        super().clean()
        if self.monthly_limit and self.monthly_limit <= 0:
            raise ValidationError({
                'monthly_limit': 'Monthly limit must be greater than zero.'
            })
        
        if self.warning_percentage >= self.critical_percentage:
            raise ValidationError({
                'warning_percentage': 'Warning percentage must be less than the critical percentage.'
            })
    
    def get_warning_amount(self):
        """Calculate the yellow alert amount"""
        return (self.monthly_limit * self.warning_percentage) / 100
    
    def get_critical_amount(self):
        """Calculate the red alert amount"""
        return (self.monthly_limit * self.critical_percentage) / 100
    
    def get_status_for_amount(self, current_amount):
        """
        Return the budget status based on the current amount
        
        Returns:
            str: 'safe', 'warning', 'critical', 'exceeded'
        """
        if current_amount >= self.monthly_limit:
            return 'exceeded'
        elif current_amount >= self.get_critical_amount():
            return 'critical'
        elif current_amount >= self.get_warning_amount():
            return 'warning'
        else:
            return 'safe'
    
    def get_percentage_used(self, current_amount):
        """Calculate the used percentage of the budget"""
        if self.monthly_limit <= 0:
            return 0
        return min(100, (current_amount / self.monthly_limit) * 100)
    
    def get_remaining_amount(self, current_amount):
        """Calculate the remaining amount of the budget"""
        return max(0, self.monthly_limit - current_amount)
    
    def __str__(self):
        return f"Budget of {self.user.username}: ₹{self.monthly_limit}/month"
