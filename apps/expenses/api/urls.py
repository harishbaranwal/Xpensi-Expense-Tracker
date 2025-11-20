"""
URLs for the REST API

This module defines the API routes that n8n will use to
obtain user data and generate reports.
"""

from django.urls import path
from .views import ActiveUsersView, UserCompleteView

app_name = 'expenses_api'

urlpatterns = [
    # Endpoint to get list of active users
    # GET /api/users/active/
    path(
        'users/active/',
        ActiveUsersView.as_view(),
        name='active-users'
    ),

    # Endpoint to get complete user data
    # GET /api/users/{user_id}/complete/
    path(
        'users/<int:id>/complete/',
        UserCompleteView.as_view(),
        name='user-complete'
    ),
]