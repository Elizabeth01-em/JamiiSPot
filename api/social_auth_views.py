from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Profile
import json
import requests
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import logging
import secrets
import string
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from django.db.models import Model
    from django.db.models.manager import Manager

logger = logging.getLogger(__name__)

@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def google_login(request):
    """
    Authenticate user with Google ID token
    """
    try:
        # Get the ID token from the request
        id_token = request.data.get('id_token')
        if not id_token:
            return Response(
                {'error': 'ID token is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify the ID token with Google
        google_response = requests.get(
            f'https://oauth2.googleapis.com/tokeninfo?id_token={id_token}'
        )
        
        if google_response.status_code != 200:
            return Response(
                {'error': 'Invalid ID token'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        google_data = google_response.json()
        
        # Check if the token is valid
        if 'email' not in google_data:
            return Response(
                {'error': 'Invalid Google token data'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        email = google_data['email']
        first_name = google_data.get('given_name', '')
        last_name = google_data.get('family_name', '')
        google_id = google_data.get('sub', '')
        
        # Check if user already exists
        try:
            user = User.objects.get(email=email)
            # Update user info if needed
            user.first_name = first_name
            user.last_name = last_name
            user.save()
        except User.DoesNotExist:
            # Create new user
            username = email.split('@')[0]
            # Ensure username is unique
            original_username = username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{original_username}_{counter}"
                counter += 1
                
            # Generate a random password using Python's secrets module
            alphabet = string.ascii_letters + string.digits + string.punctuation
            random_password = ''.join(secrets.choice(alphabet) for _ in range(12))
                
            user = User.objects.create_user(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                password=random_password  # Set a random password
            )
            
            # Create profile for the user
            Profile.objects.get_or_create(
                user=user,
                defaults={
                    'home_country': '',
                    'home_city': '',
                    'current_country': '',
                    'current_city': ''
                }
            )
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'id': user.id,  # type: ignore
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Google login error: {str(e)}")
        return Response(
            {'error': f'Google login failed: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )