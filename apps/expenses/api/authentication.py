"""
Custom authentication for the REST API using Bearer Token

This module contains the custom authentication that reuses the same
token system you already use for webhooks with n8n.
"""

from rest_framework import authentication
from rest_framework import exceptions
from django.conf import settings


class BearerTokenAuthentication(authentication.BaseAuthentication):
    """
    Custom authentication using Bearer Token for the REST API

    Uses a specific token for the API (separate from the webhook):
    - Development: 'dev-api-token-123'
    - Production: Secure token from .env.production (N8N_API_TOKEN)

    This provides better security by separating tokens by purpose:
    - N8N_WEBHOOK_TOKEN → Only for webhooks (budget 90%)
    - N8N_API_TOKEN → Only for REST API (reports)
    """
    
    def authenticate(self, request):
        """
        Authenticate the request using the Bearer Token from the Authorization header

        Args:
            request: Django HTTP request

        Returns:
            tuple: (user, token) if authentication is successful

        Raises:
            AuthenticationFailed: if no token or the token is invalid
        """

        # Get Authorization header
        auth_header = authentication.get_authorization_header(request).split()

        # Check that the header exists and has the correct format
        if not auth_header or auth_header[0].lower() != b'bearer':
            msg = 'Bearer Token required. Provide Authorization: Bearer {token}'
            raise exceptions.AuthenticationFailed(msg)

        if len(auth_header) == 1:
            msg = 'Invalid Bearer Token. No token provided.'
            raise exceptions.AuthenticationFailed(msg)
        elif len(auth_header) > 2:
            msg = 'Invalid Bearer Token. The token must not contain spaces.'
            raise exceptions.AuthenticationFailed(msg)

        # Extract the token
        token = auth_header[1].decode('utf-8')

        # Check that the token matches the one configured for the API
        expected_token = getattr(settings, 'N8N_API_TOKEN', 'dev-api-token-123')

        if token != expected_token:
            raise exceptions.AuthenticationFailed('Invalid Bearer Token.')

        # Return None as user since we use AllowAny
        # We only need to validate the token, not a specific user
        return (None, token)

    def authenticate_header(self, request):
        """
        Returns the WWW-Authenticate header for 401 responses
        """
        return 'Bearer'