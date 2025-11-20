"""
Serializers for the REST API

This module contains the serializers that convert Django models
to JSON format so that n8n can easily consume the data.
"""

from rest_framework import serializers
from django.contrib.auth.models import User
from django.db.models import Sum
from apps.expenses.models import Expense, Budget, Category
from datetime import datetime, timedelta
from django.utils import timezone


class CategorySerializer(serializers.ModelSerializer):
    """
    Serializer for expense categories
    """
    class Meta:
        model = Category
        fields = ['id', 'name',  'description']


class ExpenseSerializer(serializers.ModelSerializer):
    """
    Serializer for individual expenses
    """
    category = CategorySerializer(read_only=True)
    
    class Meta:
        model = Expense
        fields = [
            'id', 'amount', 'description', 'date', 'location', 
            'category', 'created_at', 'updated_at'
        ]


class BudgetSerializer(serializers.ModelSerializer):
    """
    Serializer for the user's budget
    """
    class Meta:
        model = Budget
        fields = [
            'monthly_limit', 'warning_percentage', 'critical_percentage',
            'email_alerts_enabled', 'created_at', 'updated_at'
        ]


class UserActiveSerializer(serializers.ModelSerializer):
    """
    Simple serializer for the list of active users
    Only includes the basic data that n8n needs to iterate
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'email']


class UserCompleteSerializer(serializers.ModelSerializer):
    """
    Complete serializer for a user with their entire history
    This is the main serializer that contains all the data
    needed by the AI to generate monthly reports
    """

    # Related fields
    budget = BudgetSerializer(read_only=True)

    # Calculated fields (defined in to_representation)
    complete_history = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 
            'date_joined', 'budget', 'complete_history'
        ]

    def get_complete_history(self, user):
        """
        Calculates and returns the user's complete expense history

        Args:
            user: User model instance

        Returns:
            dict: Complete history with expenses, summaries, and statistics
        """

        # Get all expenses for the user
        expenses = Expense.objects.filter(user=user).select_related('category').order_by('-date')

        if not expenses.exists():
            return {
                'first_expense': None,
                'last_expense': None,
                'total_months_active': 0,
                'total_expenses': 0,
                'total_expense_count': 0,
                'all_expenses': [],
                'monthly_summaries': {},
                'categories_summary': {}
            }

        # Basic data
        first_expense = expenses.last().date
        last_expense = expenses.first().date
        total_expenses = expenses.aggregate(total=Sum('amount'))['total'] or 0
        total_expense_count = expenses.count()

        # Calculate active months
        months_diff = (last_expense.year - first_expense.year) * 12 + (last_expense.month - first_expense.month)
        total_months_active = months_diff + 1

        # Serialize all expenses
        all_expenses = ExpenseSerializer(expenses, many=True).data

        # Calculate monthly summaries
        monthly_summaries = {}
        for expense in expenses:
            month_key = f"{expense.date.year}-{expense.date.month:02d}"

            if month_key not in monthly_summaries:
                monthly_summaries[month_key] = {
                    'total': 0,
                    'count': 0,
                    'categories': {}
                }

            monthly_summaries[month_key]['total'] += float(expense.amount)
            monthly_summaries[month_key]['count'] += 1

            # Group by categories within the month
            cat_name = expense.category.name
            if cat_name not in monthly_summaries[month_key]['categories']:
                monthly_summaries[month_key]['categories'][cat_name] = 0
            monthly_summaries[month_key]['categories'][cat_name] += float(expense.amount)

        # Calculate category summary (total history)
        categories_summary = {}
        for expense in expenses:
            cat_name = expense.category.name
            if cat_name not in categories_summary:
                categories_summary[cat_name] = {
                    'total': 0,
                    'count': 0,
                    'percentage': 0
                }

            categories_summary[cat_name]['total'] += float(expense.amount)
            categories_summary[cat_name]['count'] += 1

        # Calculate percentages
        for cat_name in categories_summary:
            categories_summary[cat_name]['percentage'] = round(
                (categories_summary[cat_name]['total'] / float(total_expenses)) * 100, 2
            )

        return {
            'first_expense': first_expense.isoformat(),
            'last_expense': last_expense.isoformat(),
            'total_months_active': total_months_active,
            'total_expenses': float(total_expenses),
            'total_expense_count': total_expense_count,
            'all_expenses': all_expenses,
            'monthly_summaries': monthly_summaries,
            'categories_summary': categories_summary
        }