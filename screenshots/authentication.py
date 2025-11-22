import logging

import jwt
from django.conf import settings
from django.contrib.auth.models import User
from jwt import PyJWKClient
from rest_framework import authentication, exceptions

logger = logging.getLogger(__name__)

# Django's default max_length for username
USERNAME_MAX_LENGTH = 150


class MultiProviderJWTAuthentication(authentication.BaseAuthentication):
    """
    JWT authentication supporting multiple OIDC providers (GitLab, GitHub, etc.)

    Uses the 'iss' (issuer) claim in the JWT to determine which provider issued the token
    and validates against the appropriate JWKS endpoint.
    """

    # Map of issuer URLs to their JWKS endpoints
    PROVIDER_JWKS_ENDPOINTS = {
        "https://gitlab.com": "https://gitlab.com/oauth/discovery/keys",
        "https://github.com": "https://token.actions.githubusercontent.com/.well-known/jwks",
    }

    def authenticate(self, request):
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")

        if not auth_header.startswith("Bearer "):
            return None

        parts = auth_header.split(" ", 1)
        if len(parts) != 2:
            return None
        token = parts[1]

        try:
            # Decode without verification first to get the issuer
            unverified = jwt.decode(token, options={"verify_signature": False})
            issuer = unverified.get("iss")

            if not issuer:
                raise exceptions.AuthenticationFailed("Token missing issuer claim")

            # Get JWKS endpoint for this issuer
            jwks_url = self.PROVIDER_JWKS_ENDPOINTS.get(issuer)
            if not jwks_url:
                # Check if it's a custom provider from settings
                custom_providers = getattr(settings, "OIDC_PROVIDERS", {})
                provider_config = custom_providers.get(issuer)
                if provider_config:
                    jwks_url = provider_config.get("jwks_endpoint")

                if not jwks_url:
                    raise exceptions.AuthenticationFailed(f"Unknown token issuer: {issuer}")

            # Fetch public keys and verify token
            jwks_client = PyJWKClient(jwks_url)
            signing_key = jwks_client.get_signing_key_from_jwt(token)

            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256", "RS384", "RS512"],
                audience=None,  # You may want to validate audience in production
                options={"verify_aud": False},
            )

            # Validate project authorization if needed
            if not self.is_authorized(payload, request):
                raise exceptions.AuthenticationFailed("Token not authorized for this action")

            # Get or create user based on the token
            user = self.get_or_create_user(payload)

            return (user, payload)

        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {e}")
            raise exceptions.AuthenticationFailed("Invalid token")
        except Exception as e:
            logger.error(f"JWT authentication error: {e}")
            raise exceptions.AuthenticationFailed(str(e))

    def is_authorized(self, payload, request):
        """
        Check if the JWT token is authorized to perform the requested action.

        For GitLab CI/CD, you might check:
        - project_id or project_path matches allowed projects
        - pipeline_source is valid
        - ref (branch) is authorized

        Customize this based on your authorization requirements.
        """
        # Example: Check if project is in allowed list
        allowed_projects = getattr(settings, "OIDC_ALLOWED_PROJECTS", None)
        if allowed_projects:
            project_path = payload.get("project_path") or payload.get("repository")
            if project_path not in allowed_projects:
                return False

        # By default, allow all authenticated tokens
        return True

    def get_or_create_user(self, payload):
        """
        Get or create a Django user based on JWT payload.

        Different providers have different claim structures:
        - GitLab: 'sub' is numeric user ID, 'user_login' is username
        - GitHub: 'sub' contains repo info, 'actor' is username
        """
        # Try to extract username from various claim names
        username = (
            payload.get("user_login")  # GitLab
            or payload.get("actor")  # GitHub Actions
            or payload.get("email")  # Generic
            or f"ci-user-{payload.get('sub', 'unknown')}"
        )

        # Normalize username to Django's max length
        username = username[:USERNAME_MAX_LENGTH]

        # Get or create user
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "email": payload.get("user_email", ""),
                "first_name": payload.get("name", "")[:30],
            },
        )

        if created:
            logger.info(f"Created new user from JWT: {username}")

        return user
