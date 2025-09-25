# api/discovery_views.py

from django.contrib.auth.models import User
from django.db.models import Q
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import logging
from typing import Any, Dict, List, Tuple, Optional

from .models import Profile
from .serializers import ProfileSerializer, UserSerializer
from .matching import TravelerMatcher, DiscoveryStats

logger = logging.getLogger(__name__)

class DiscoveryViewSet(viewsets.ViewSet):
    """
    API endpoints for discovering countrymates and travel connections.
    This implements the core app vision: connecting people from same country abroad.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_user_profile(self):
        """Helper method to get current user's profile"""
        try:
            return self.request.user.profile
        except Exception:
            return None

    @action(detail=False, methods=['get'], url_path='countrymates-nearby')
    def countrymates_nearby(self, request):
        """
        Find people from your home country in your current location.
        This is the CORE feature of the app.
        
        GET /api/discover/countrymates-nearby/
        """
        user_profile = self.get_user_profile()
        if not user_profile:
            return Response({'error': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Find nearby countrymates
        countrymates = TravelerMatcher.find_countrymates_nearby(user_profile)
        
        # Get statistics
        stats = DiscoveryStats.get_location_stats(user_profile)
        
        # Serialize the data
        serializer = ProfileSerializer(countrymates, many=True, context={'request': request})
        
        # Send notification about discovery activity
        self.send_discovery_notification(
            request.user.id,
            'location_search_performed',
            f'Found {countrymates.count()} people from {user_profile.home_country}',
            {
                'search_type': 'countrymates_nearby',
                'results_count': countrymates.count(),
                'location': f"{user_profile.current_city}, {user_profile.current_country}"
            }
        )
        
        return Response({
            'message': f'Found {countrymates.count()} people from {user_profile.home_country} in {user_profile.current_city}',
            'location': {
                'home_country': user_profile.home_country,
                'current_location': f"{user_profile.current_city}, {user_profile.current_country}"
            },
            'statistics': stats,
            'countrymates': serializer.data
        })
    
    @action(detail=False, methods=['get'], url_path='local-experts')
    def local_experts(self, request):
        """
        Find verified local experts who can help travelers.
        
        GET /api/discover/local-experts/
        """
        user_profile = self.get_user_profile()
        if not user_profile:
            return Response({'error': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)
        
        experts = TravelerMatcher.find_local_experts(user_profile)
        serializer = ProfileSerializer(experts, many=True, context={'request': request})
        
        return Response({
            'message': f'Found {experts.count()} local experts in {user_profile.current_city}',
            'location': f"{user_profile.current_city}, {user_profile.current_country}",
            'experts': serializer.data
        })
    
    @action(detail=False, methods=['get'], url_path='travel-buddies')
    def travel_buddies(self, request):
        """
        Find fellow travelers from your country with overlapping travel dates.
        
        GET /api/discover/travel-buddies/
        """
        user_profile = self.get_user_profile()
        if not user_profile:
            return Response({'error': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)
        
        if user_profile.travel_status != 'traveling':
            return Response({
                'message': 'You need to set your travel status to "traveling" to find travel buddies',
                'travel_status': user_profile.travel_status,
                'travel_buddies': []
            })
        
        travel_buddies = TravelerMatcher.find_travel_buddies(user_profile)
        serializer = ProfileSerializer(travel_buddies, many=True, context={'request': request})
        
        return Response({
            'message': f'Found {travel_buddies.count()} potential travel buddies',
            'your_travel_dates': {
                'start': user_profile.travel_start_date,
                'end': user_profile.travel_end_date
            },
            'travel_buddies': serializer.data
        })
    
    @action(detail=False, methods=['get'], url_path='smart-matches')
    def smart_matches(self, request):
        """
        AI-powered matching that considers multiple compatibility factors.
        
        GET /api/discover/smart-matches/?limit=20
        """
        user_profile = self.get_user_profile()
        if not user_profile:
            return Response({'error': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Get limit from query params
        limit = int(request.query_params.get('limit', 20))
        limit = min(limit, 50)  # Max 50 for performance
        
        # Get smart matches with scores and reasons
        matches = TravelerMatcher.get_smart_matches(user_profile, limit=limit)
        
        # Format the response
        formatted_matches: List[Dict[str, Any]] = []
        for profile, score, reasons in matches:
            serializer_data = ProfileSerializer(profile, context={'request': request}).data
            profile_data: Dict[str, Any] = dict(serializer_data)
            profile_data['compatibility_score'] = score
            profile_data['match_reasons'] = reasons
            formatted_matches.append(profile_data)
        
        return Response({
            'message': f'Found {len(formatted_matches)} smart matches for you',
            'matching_criteria': {
                'home_country': user_profile.home_country,
                'current_location': f"{user_profile.current_city}, {user_profile.current_country}",
                'travel_status': user_profile.travel_status
            },
            'matches': formatted_matches
        })
    
    @action(detail=False, methods=['get'], url_path='emergency-network')
    def emergency_network(self, request):
        """
        Find trusted countrymates who can help in emergencies.
        
        GET /api/discover/emergency-network/
        """
        user_profile = self.get_user_profile()
        if not user_profile:
            return Response({'error': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)
        
        emergency_contacts = TravelerMatcher.get_emergency_network(user_profile)
        serializer = ProfileSerializer(emergency_contacts, many=True, context={'request': request})
        
        return Response({
            'message': f'Your emergency network: {emergency_contacts.count()} trusted countrymates',
            'location': f"{user_profile.current_city}, {user_profile.current_country}",
            'emergency_contacts': serializer.data,
            'note': 'These are fellow countrymates who are available to help in your area'
        })
    
    @action(detail=False, methods=['get'], url_path='location-stats')
    def location_stats(self, request):
        """
        Get statistics about your countrymates in current location.
        
        GET /api/discover/location-stats/
        """
        user_profile = self.get_user_profile()
        if not user_profile:
            return Response({'error': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)
        
        stats = DiscoveryStats.get_location_stats(user_profile)
        global_network = DiscoveryStats.get_global_network_size(user_profile.home_country)
        
        return Response({
            'location': {
                'home_country': user_profile.home_country,
                'current_location': f"{user_profile.current_city}, {user_profile.current_country}"
            },
            'local_network': stats,
            'global_network_size': global_network,
            'insights': self.generate_location_insights(stats, user_profile)
        })
    
    @action(detail=False, methods=['post'], url_path='update-travel-status')
    def update_travel_status(self, request):
        """
        Update your travel status and dates.
        
        POST /api/discover/update-travel-status/
        {
            "travel_status": "traveling",
            "travel_start_date": "2025-01-15",
            "travel_end_date": "2025-01-30",
            "is_available_to_help": true
        }
        """
        user_profile = self.get_user_profile()
        if not user_profile:
            return Response({'error': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Validate and update travel status
        travel_status = request.data.get('travel_status')
        if travel_status and travel_status in dict(Profile.TRAVEL_STATUS_CHOICES):
            user_profile.travel_status = travel_status
        
        # Update travel dates if provided
        if 'travel_start_date' in request.data:
            user_profile.travel_start_date = request.data['travel_start_date']
        
        if 'travel_end_date' in request.data:
            user_profile.travel_end_date = request.data['travel_end_date']
        
        if 'is_available_to_help' in request.data:
            user_profile.is_available_to_help = request.data['is_available_to_help']
        
        user_profile.save()
        
        # Send notification about status change
        self.send_travel_status_notification(user_profile)
        
        return Response({
            'message': 'Travel status updated successfully',
            'travel_status': user_profile.travel_status,
            'travel_dates': {
                'start': user_profile.travel_start_date,
                'end': user_profile.travel_end_date
            },
            'available_to_help': user_profile.is_available_to_help
        })
    
    def generate_location_insights(self, stats, user_profile):
        """Generate helpful insights about the local network"""
        insights = []
        
        total = stats['total_countrymates']
        if total == 0:
            insights.append(f"You're the first person from {user_profile.home_country} we've found in {user_profile.current_city}!")
        elif total < 5:
            insights.append(f"Small but growing community: {total} people from {user_profile.home_country}")
        elif total < 20:
            insights.append(f"Active community: {total} people from {user_profile.home_country}")
        else:
            insights.append(f"Large community: {total} people from {user_profile.home_country}")
        
        if stats['travelers'] > 0:
            insights.append(f"{stats['travelers']} fellow travelers currently in the area")
        
        if stats['local_experts'] > 0:
            insights.append(f"{stats['local_experts']} verified local experts available to help")
        
        if stats['available_helpers'] > stats['total_countrymates'] * 0.7:
            insights.append("Very helpful community - most people are available to help!")
        
        return insights
    
    def send_discovery_notification(self, user_id, notification_type, message, data=None):
        """Send WebSocket notification for discovery activity"""
        try:
            channel_layer = get_channel_layer()
            if channel_layer is not None:
                user_group = f"user_{user_id}"
                
                async_to_sync(channel_layer.group_send)(
                    user_group,
                    {
                        'type': 'send_notification',
                        'notification_type': notification_type,
                        'message': message,
                        'data': data or {}
                    }
                )
        except Exception as e:
            logger.error(f"Failed to send discovery notification: {e}")
    
    def send_travel_status_notification(self, user_profile):
        """Notify nearby countrymates when user updates travel status"""
        try:
            # Find nearby countrymates to notify
            nearby_countrymates = TravelerMatcher.find_countrymates_nearby(user_profile)
            
            channel_layer = get_channel_layer()
            if channel_layer is not None:
                for countrymate_profile in nearby_countrymates:
                    user_group = f"user_{countrymate_profile.user.id}"
                    
                    # Determine notification message based on travel status
                    if user_profile.travel_status == 'traveling':
                        message = f"{user_profile.user.username} from {user_profile.home_country} is now traveling in your area"
                        notification_type = 'countrymate_traveling_nearby'
                    elif user_profile.travel_status == 'resident':
                        message = f"{user_profile.user.username} from {user_profile.home_country} is now a local resident in your area"
                        notification_type = 'countrymate_became_resident'
                    else:
                        message = f"{user_profile.user.username} from {user_profile.home_country} updated their travel status"
                        notification_type = 'countrymate_status_update'
                    
                    async_to_sync(channel_layer.group_send)(
                        user_group,
                        {
                            'type': 'send_notification',
                            'notification_type': notification_type,
                            'message': message,
                            'data': {
                                'user_id': user_profile.user.id,
                                'username': user_profile.user.username,
                                'home_country': user_profile.home_country,
                                'travel_status': user_profile.travel_status,
                                'current_location': f"{user_profile.current_city}, {user_profile.current_country}",
                                'available_to_help': user_profile.is_available_to_help,
                                'travel_dates': {
                                    'start': user_profile.travel_start_date.isoformat() if user_profile.travel_start_date else None,
                                    'end': user_profile.travel_end_date.isoformat() if user_profile.travel_end_date else None
                                }
                            }
                        }
                    )
            
            logger.info(f"Notified {nearby_countrymates.count()} countrymates about {user_profile.user.username}'s travel status update")
                
        except Exception as e:
            logger.error(f"Failed to send travel status notification: {e}")

class TravelStatusViewSet(viewsets.ViewSet):
    """
    Dedicated endpoints for managing travel status and preferences.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'], url_path='my-status')
    def my_status(self, request):
        """
        Get current user's travel status and preferences.
        
        GET /api/travel-status/my-status/
        """
        try:
            profile = request.user.profile
            return Response({
                'travel_status': profile.travel_status,
                'travel_dates': {
                    'start': profile.travel_start_date,
                    'end': profile.travel_end_date
                },
                'location': {
                    'home_country': profile.home_country,
                    'home_city': profile.home_city,
                    'current_country': profile.current_country,
                    'current_city': profile.current_city
                },
                'preferences': {
                    'is_available_to_help': profile.is_available_to_help,
                    'is_local_expert': profile.is_local_expert,
                    'languages_spoken': profile.languages_spoken,
                    'expertise_areas': profile.expertise_areas
                },
                'stats': {
                    'helper_rating': float(profile.helper_rating),
                    'help_requests_fulfilled': profile.help_requests_fulfilled,
                    'years_in_current_location': profile.years_in_current_location
                }
            })
        except Exception:
            return Response({'error': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['post'], url_path='update-preferences')
    def update_preferences(self, request):
        """
        Update travel preferences and helper settings.
        
        POST /api/travel-status/update-preferences/
        {
            "is_available_to_help": true,
            "is_local_expert": false,
            "languages_spoken": ["English", "Swahili"],
            "expertise_areas": ["food", "transportation"],
            "years_in_current_location": 3
        }
        """
        try:
            profile = request.user.profile
            
            # Update preferences
            if 'is_available_to_help' in request.data:
                profile.is_available_to_help = request.data['is_available_to_help']
            
            if 'is_local_expert' in request.data:
                profile.is_local_expert = request.data['is_local_expert']
            
            if 'languages_spoken' in request.data:
                profile.languages_spoken = request.data['languages_spoken']
            
            if 'expertise_areas' in request.data:
                profile.expertise_areas = request.data['expertise_areas']
                
            if 'years_in_current_location' in request.data:
                profile.years_in_current_location = request.data['years_in_current_location']
            
            profile.save()
            
            return Response({
                'message': 'Preferences updated successfully',
                'preferences': {
                    'is_available_to_help': profile.is_available_to_help,
                    'is_local_expert': profile.is_local_expert,
                    'languages_spoken': profile.languages_spoken,
                    'expertise_areas': profile.expertise_areas,
                    'years_in_current_location': profile.years_in_current_location
                }
            })
            
        except Exception:
            return Response({'error': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)