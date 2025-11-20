from django.contrib import admin
from .models import Category, Expense, Budget


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Admin to manage expense categories"""
    list_display = ['name', 'icon', 'color', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'description']
    ordering = ['name']
    fields = ['name', 'icon', 'color', 'description']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    """Admin to manage individual expenses"""
    list_display = ['date', 'amount', 'category', 'user', 'description']
    list_filter = ['category', 'date', 'user', 'created_at']
    search_fields = ['description', 'location']
    ordering = ['-date', '-created_at']  
    date_hierarchy = 'date'
    fields = ['user', 'category', 'amount', 'date', 'description', 'location']
    readonly_fields = ['created_at', 'updated_at']
    autocomplete_fields = ['category']  # For quick search


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    """Admin to manage user budgets"""
    list_display = ['user', 'monthly_limit', 'warning_percentage', 'critical_percentage', 'email_alerts_enabled', 'created_at']
    list_filter = ['email_alerts_enabled', 'created_at', 'updated_at']
    search_fields = ['user__username', 'user__email']
    ordering = ['-created_at']
    fields = ['user', 'monthly_limit', 'warning_percentage', 'critical_percentage', 'email_alerts_enabled']
    readonly_fields = ['created_at', 'updated_at']
    autocomplete_fields = ['user']  # For quick user search
