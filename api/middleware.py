# api/middleware.py

import logging
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from urllib.parse import parse_qs

logger = logging.getLogger(__name__)

@database_sync_to_async
def get_user(user_id):
    # Import User model inside the function 
    from django.contrib.auth.models import User 
    try:
        user = User.objects.get(id=user_id)
        logger.info(f"Found authenticated user: {user.username} (ID: {user.id})")
        return user
    except User.DoesNotExist:
        logger.warning(f"User with ID {user_id} not found")
        return AnonymousUser()

class JwtAuthMiddleware:
    """
    Custom middleware to authenticate users for WebSocket connections
    using a JWT token from the query string.
    """
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        query_string = scope.get('query_string', b'').decode()
        query_params = parse_qs(query_string)
        token = query_params.get('token', [None])[0]
        
        logger.info(f"WebSocket connection attempt with query string: {query_string}")

        if token:
            # Remove angle brackets if present
            token = token.strip('<>')
            logger.info(f"Processing token: {token[:50]}...")
            
            try:
                access_token = AccessToken(token)
                user_id = access_token['user_id']
                logger.info(f"Token is valid for user_id: {user_id}")
                scope['user'] = await get_user(user_id)
            except (InvalidToken, TokenError) as e:
                logger.error(f"Token validation failed: {e}")
                scope['user'] = AnonymousUser()
            except Exception as e:
                logger.error(f"Unexpected error during token validation: {e}")
                scope['user'] = AnonymousUser()
        else:
            logger.info("No token provided in query parameters")
            scope['user'] = AnonymousUser()
        
        logger.info(f"Final user in scope: {scope['user']}")
        return await self.app(scope, receive, send)