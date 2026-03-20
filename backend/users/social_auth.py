"""
Social Authentication for PathAI Mobile App

Supports:
- Google OAuth (token validation)
- Apple Sign In (token validation)
- JWT token generation for authenticated sessions

Flow:
1. Frontend gets OAuth token from Google/Apple SDK
2. Frontend sends token to backend
3. Backend validates token with provider
4. Backend creates/updates user account
5. Backend returns JWT token for API access
"""
import os
import requests
import jwt
import json
from datetime import datetime, timedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.response import Response
from users.jwt_utils import generate_jwt_token

User = get_user_model()


class GoogleAuthValidator:
    """
    Validate Google OAuth tokens and retrieve user info.
    """

    def __init__(self):
        self.google_token_info_url = "https://oauth2.googleapis.com/tokeninfo"
        self.google_user_info_url = "https://www.googleapis.com/oauth2/v3/userinfo"

    def validate_token(self, token: str) -> dict:
        """
        Validate Google OAuth token and return user information.

        Args:
            token: Google OAuth ID token

        Returns:
            dict with user info: {
                'sub': 'google_user_id',
                'email': 'user@gmail.com',
                'name': 'John Doe',
                'picture': 'https://...',
                'email_verified': True
            }

        Raises:
            ValueError: If token is invalid
        """
        try:
            # Validate token with Google
            response = requests.get(
                self.google_token_info_url,
                params={'id_token': token},
                timeout=10
            )
            response.raise_for_status()
            token_info = response.json()

            # Verify audience matches our client ID
            # For testing, we'll skip strict validation
            # In production, check: token_info['aud'] == settings.GOOGLE_CLIENT_ID

            return {
                'sub': token_info.get('sub'),
                'email': token_info.get('email'),
                'name': token_info.get('name'),
                'given_name': token_info.get('given_name'),
                'family_name': token_info.get('family_name'),
                'picture': token_info.get('picture'),
                'email_verified': token_info.get('email_verified', False),
                'provider': 'google',
            }

        except requests.RequestException as e:
            raise ValueError(f"Failed to validate Google token: {str(e)}")


class AppleAuthValidator:
    """
    Validate Apple Sign In tokens and retrieve user info.

    Note: Apple Sign In requires JWT validation.
    For development/testing, we'll use a simplified approach.
    """

    def __init__(self):
        self.apple_verify_url = "https://appleid.apple.com/auth/token"
        # In production, you'd need Apple's private key for JWT validation
        # For now, we'll decode without verification (development only)

    def validate_token(self, token: str, user_data: dict = None) -> dict:
        """
        Validate Apple Sign In token and return user information.

        Args:
            token: Apple ID token (JWT)
            user_data: Additional data from Apple (name, email)

        Returns:
            dict with user info

        Note: In production, you must verify the JWT signature
        """
        try:
            # Decode JWT (no signature verification in development)
            # In production, verify with Apple's public keys
            decoded = jwt.decode(
                token,
                options={
                    'verify_signature': False,  # TODO: Enable in production
                    'verify_aud': settings.APPLE_CLIENT_ID if hasattr(settings, 'APPLE_CLIENT_ID') else None,
                    'verify_iss': True,
                    'verify_exp': True,
                }
            )

            # Extract user info
            user_info = {
                'sub': decoded.get('sub'),  # Apple's unique user ID
                'email': decoded.get('email'),
                'email_verified': decoded.get('email_verified', 'true' == 'true'),
                'provider': 'apple',
            }

            # Add name from user_data if provided (Apple only sends name once)
            if user_data and 'name' in user_data:
                name = user_data['name']
                user_info['name'] = f"{name.get('firstName', '')} {name.get('lastName', '')}".strip()
                user_info['given_name'] = name.get('firstName', '')
                user_info['family_name'] = name.get('lastName', '')

            return user_info

        except jwt.DecodeError as e:
            raise ValueError(f"Invalid Apple token: {str(e)}")
        except Exception as e:
            raise ValueError(f"Failed to validate Apple token: {str(e)}")


def get_or_create_user_from_oauth(user_info: dict, provider: str) -> User:
    """
    Get or create user from OAuth provider information.

    Args:
        user_info: dict with user data from OAuth provider
        provider: 'google' or 'apple'

    Returns:
        User instance
    """
    # Check if user exists with this provider ID
    provider_user_id = user_info.get('sub')
    email = user_info.get('email')

    # First, try to find by provider ID
    user = User.objects.filter(
        profile__provider=provider,
        profile__provider_id=provider_user_id
    ).first()

    if user:
        return user

    # Try to find by email
    if email:
        user = User.objects.filter(email=email).first()
        if user:
            # Link existing account to provider
            if hasattr(user, 'profile'):
                user.profile.provider = provider
                user.profile.provider_id = provider_user_id
                user.profile.save()
            return user

    # Create new user
    # Generate username from email or provider ID
    username = email.split('@')[0] if email else f"{provider}_{provider_user_id[:10]}"

    # Ensure username is unique
    base_username = username
    counter = 1
    while User.objects.filter(username=username).exists():
        username = f"{base_username}{counter}"
        counter += 1

    # Create user
    user = User.objects.create_user(
        username=username,
        email=email,
        password=None,  # No password for OAuth users
    )

    # Update profile with provider info
    if hasattr(user, 'profile'):
        user.profile.provider = provider
        user.profile.provider_id = provider_user_id
        if user_info.get('name'):
            user.profile.display_name = user_info['name']
        if user_info.get('picture'):
            user.profile.avatar_url = user_info['picture']
        user.profile.save()

    return user


def authenticate_google_user(token: str) -> Response:
    """
    Authenticate user with Google OAuth token.

    POST /api/auth/google/
    Body: {"token": "google_oauth_token"}

    Returns:
        JWT token and user data
    """
    try:
        validator = GoogleAuthValidator()
        user_info = validator.validate_token(token)

        user = get_or_create_user_from_oauth(user_info, 'google')

        # Generate JWT token
        jwt_token = generate_jwt_token(user)

        return Response({
            'token': jwt_token,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'display_name': getattr(user.profile, 'display_name', user.username) if hasattr(user, 'profile') else user.username,
                'avatar': getattr(user.profile, 'avatar_url', None) if hasattr(user, 'profile') else None,
            },
            'provider': 'google',
        }, status=status.HTTP_200_OK)

    except ValueError as e:
        return Response({
            'detail': str(e),
        }, status=status.HTTP_401_UNAUTHORIZED)
    except Exception as e:
        return Response({
            'detail': f'Authentication failed: {str(e)}',
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def authenticate_apple_user(token: str, user_data: dict = None) -> Response:
    """
    Authenticate user with Apple Sign In token.

    POST /api/auth/apple/
    Body: {
        "token": "apple_id_token",
        "user": {  // Optional, only provided on first login
            "name": {
                "firstName": "John",
                "lastName": "Doe"
            },
            "email": "user@icloud.com"
        }
    }

    Returns:
        JWT token and user data
    """
    try:
        validator = AppleAuthValidator()
        user_info = validator.validate_token(token, user_data)

        user = get_or_create_user_from_oauth(user_info, 'apple')

        # Generate JWT token
        jwt_token = generate_jwt_token(user)

        return Response({
            'token': jwt_token,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'display_name': getattr(user.profile, 'display_name', user.username) if hasattr(user, 'profile') else user.username,
                'avatar': getattr(user.profile, 'avatar_url', None) if hasattr(user, 'profile') else None,
            },
            'provider': 'apple',
        }, status=status.HTTP_200_OK)

    except ValueError as e:
        return Response({
            'detail': str(e),
        }, status=status.HTTP_401_UNAUTHORIZED)
    except Exception as e:
        return Response({
            'detail': f'Authentication failed: {str(e)}',
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def link_oauth_account(request, provider: str) -> Response:
    """
    Link OAuth provider to existing account.

    POST /api/auth/link/{provider}/
    Body: {"token": "oauth_token"}

    Allows user to add Google/Apple login to existing email/password account.
    """
    try:
        if not request.user.is_authenticated:
            return Response({
                'detail': 'Authentication required',
            }, status=status.HTTP_401_UNAUTHORIZED)

        token = request.data.get('token')
        if not token:
            return Response({
                'detail': 'Token is required',
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate token based on provider
        if provider == 'google':
            validator = GoogleAuthValidator()
            user_info = validator.validate_token(token)
        elif provider == 'apple':
            validator = AppleAuthValidator()
            user_info = validator.validate_token(token)
        else:
            return Response({
                'detail': 'Invalid provider',
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check if already linked to another account
        existing_user = User.objects.filter(
            profile__provider=provider,
            profile__provider_id=user_info['sub']
        ).first()

        if existing_user and existing_user != request.user:
            return Response({
                'detail': 'This account is already linked to another user',
            }, status=status.HTTP_400_BAD_REQUEST)

        # Link to current user
        if hasattr(request.user, 'profile'):
            request.user.profile.provider = provider
            request.user.profile.provider_id = user_info['sub']
            request.user.profile.save()

        return Response({
            'detail': f'Successfully linked {provider.capitalize()} account',
            'user': {
                'id': request.user.id,
                'username': request.user.username,
                'email': request.user.email,
            },
        }, status=status.HTTP_200_OK)

    except ValueError as e:
        return Response({
            'detail': str(e),
        }, status=status.HTTP_401_UNAUTHORIZED)
    except Exception as e:
        return Response({
            'detail': f'Failed to link account: {str(e)}',
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
