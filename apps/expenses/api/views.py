"""
Views for the REST API

This module contains the views that handle the API endpoints
so that n8n can obtain the necessary data for reports.
"""

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.contrib.auth.models import User
from django.db.models import Exists, OuterRef
from django.utils import timezone
from datetime import timedelta
from apps.expenses.models import Expense, Budget
from .serializers import UserActiveSerializer, UserCompleteSerializer
from .authentication import BearerTokenAuthentication


class ActiveUsersView(generics.ListAPIView):
    """
    View to get the list of active users

    Endpoint: GET /api/users/active/

    Criteria for "active user":
    - Has a configured budget (Budget exists)
    - Has email alerts enabled (email_alerts_enabled=True)
    - Has recorded expenses in the last 30 days

    Response:
    [
        {
            "id": 1,
            "username": "john",
            "email": "john@email.com"
        },
        ...
    ]
    """
    
    serializer_class = UserActiveSerializer
    authentication_classes = [BearerTokenAuthentication]
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        """
        Returns the users that meet the criteria for "active"

        Returns:
            QuerySet: Filtered active users
        """

        # Cutoff date for recent expenses (last 30 days)
        thirty_days_ago = timezone.now().date() - timedelta(days=30)

        # Filter users who:
        # 1. Have a configured budget
        # 2. Have email alerts enabled
        # 3. Have recorded expenses in the last 30 days
        active_users = User.objects.filter(
            # Has a configured budget
            budget__isnull=False,
            # Has email alerts enabled
            budget__email_alerts_enabled=True,
            # Has recorded expenses in the last 30 days
            expenses__date__gte=thirty_days_ago
        ).distinct().order_by('username')

        return active_users
    
    def list(self, request, *args, **kwargs):
        """
        Handles the GET request and returns the list of active users

        Args:
            request: HTTP request

        Returns:
            Response: List of active users in JSON format
        """

        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        # Add additional info useful for n8n
        response_data = {
            'users': serializer.data,
            'total_active_users': queryset.count(),
            'timestamp': timezone.now().isoformat(),
            'criteria': {
                'has_budget': True,
                'email_alerts_enabled': True,
                'recent_expenses_days': 30
            }
        }

        return Response(response_data, status=status.HTTP_200_OK)


class UserCompleteView(generics.RetrieveAPIView):
    """
    View to get the complete data of a specific user

    Endpoint: GET /api/users/{user_id}/complete/

    Includes:
    - User data
    - Configured budget
    - Complete expense history
    - Monthly summaries
    - Category summaries

    Response:
    {
        "user": { ... },
        "budget": { ... },
        "complete_history": {
            "all_expenses": [ ... ],
            "monthly_summaries": { ... },
            "categories_summary": { ... }
        }
    }
    """
    
    serializer_class = UserCompleteSerializer
    authentication_classes = [BearerTokenAuthentication]
    permission_classes = [AllowAny]
    lookup_field = 'id'
    
    def get_queryset(self):
        """
        Returns the users that have data to show

        Returns:
            QuerySet: Users with configured budget
        """

        # Only return users with a configured budget
        # (no point in generating reports without a budget)
        return User.objects.filter(
            budget__isnull=False
        ).select_related('budget')
    
    def retrieve(self, request, *args, **kwargs):
        """
        Handles the GET request and returns the complete user data

        Args:
            request: HTTP request

        Returns:
            Response: Complete user data in JSON format
        """

        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)

            # Add metadata useful for n8n
            response_data = {
                **serializer.data,
                'metadata': {
                    'generated_at': timezone.now().isoformat(),
                    'api_version': '1.0',
                    'data_complete': True
                }
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response(
                {
                    'error': 'User not found or does not have a configured budget',
                    'detail': 'The user must have a configured budget to generate reports'
                },
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {
                    'error': 'Internal server error',
                    'detail': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )