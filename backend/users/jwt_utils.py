"""
JWT token utilities for PathAI authentication.

Wraps rest_framework_simplejwt for consistent token generation.
"""
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model

User = get_user_model()


def generate_jwt_token(user):
    """
    Generate JWT access and refresh tokens for a user.

    Args:
        user: User instance

    Returns:
        str: JWT access token
    """
    refresh = RefreshToken.for_user(user)
    return str(refresh.access_token)


def generate_jwt_token_pair(user):
    """
    Generate both access and refresh JWT tokens for a user.

    Args:
        user: User instance

    Returns:
        dict: {
            'access': str,
            'refresh': str
        }
    """
    refresh = RefreshToken.for_user(user)
    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh),
    }
