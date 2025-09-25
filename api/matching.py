# api/matching.py

from django.db.models import Q, Count
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import logging

from .models import Profile

logger = logging.getLogger(__name__)

class TravelerMatcher:
    """
    Smart matching algorithm for travelers and locals based on:
    1. Location matching (same home country, same current location)
    2. Travel status compatibility
    3. Common interests
    4. Language compatibility
    5. Availability to help
    6. Local expertise
    """
    
    @staticmethod
    def find_countrymates_nearby(user_profile, include_self=False):
        """
        Find people from the same home country in the same current location.
        This is the CORE feature for the app vision.
        """
        queryset = Profile.objects.filter(
            home_country=user_profile.home_country,           # Same home country
            current_country=user_profile.current_country,     # Same current location
            current_city=user_profile.current_city            # Same current city
        ).select_related('user')
        
        if not include_self:
            queryset = queryset.exclude(user=user_profile.user)
        
        return queryset.order_by('-user__last_login')
    
    @staticmethod
    def find_local_experts(user_profile):
        """
        Find verified locals who can help travelers from the user's country.
        """
        return Profile.objects.filter(
            current_country=user_profile.current_country,      # In user's current location
            current_city=user_profile.current_city,
            is_local_expert=True,                              # Marked as local expert
            is_available_to_help=True,                         # Available to help
            years_in_current_location__gte=1                   # Been there at least 1 year
        ).exclude(
            user=user_profile.user
        ).select_related('user').order_by('-helper_rating', '-help_requests_fulfilled')
    
    @staticmethod
    def find_travel_buddies(user_profile):
        """
        Find other travelers from same country who are traveling at the same time.
        """
        if user_profile.travel_status != 'traveling':
            return Profile.objects.none()
        
        # Find other travelers from same country
        base_query = Profile.objects.filter(
            home_country=user_profile.home_country,
            current_country=user_profile.current_country,
            travel_status='traveling'
        ).exclude(user=user_profile.user)
        
        # If user has travel dates, find overlapping travelers
        if user_profile.travel_start_date and user_profile.travel_end_date:
            overlapping_travelers = base_query.filter(
                Q(travel_start_date__lte=user_profile.travel_end_date) &
                Q(travel_end_date__gte=user_profile.travel_start_date)
            )
            return overlapping_travelers.select_related('user')
        
        # Otherwise, return all travelers from same country in same location
        return base_query.select_related('user')
    
    @staticmethod
    def get_smart_matches(user_profile, limit=20):
        """
        AI-powered matching that combines multiple factors for best recommendations.
        Returns a list of tuples: (profile, score, match_reasons)
        """
        # Start with basic location matching
        base_matches = TravelerMatcher.find_countrymates_nearby(user_profile)
        
        scored_matches = []
        
        for match_profile in base_matches[:50]:  # Limit for performance
            score, reasons = TravelerMatcher.calculate_compatibility_score(
                user_profile, match_profile
            )
            
            if score > 0:  # Only include matches with positive scores
                scored_matches.append((match_profile, score, reasons))
        
        # Sort by score (descending) and return top matches
        scored_matches.sort(key=lambda x: x[1], reverse=True)
        return scored_matches[:limit]
    
    @staticmethod
    def calculate_compatibility_score(profile1, profile2):
        """
        Calculate compatibility score between two profiles.
        Returns (score, reasons_list)
        """
        score = 0
        reasons = []
        
        # Base score for being countrymates in same location
        score += 50
        reasons.append("From your home country")
        
        # Travel status compatibility
        travel_bonus, travel_reason = TravelerMatcher._calculate_travel_compatibility(
            profile1, profile2
        )
        score += travel_bonus
        if travel_reason:
            reasons.append(travel_reason)
        
        # Common interests (+15 points each)
        profile1_interests = set(profile1.interests.values_list('id', flat=True))
        profile2_interests = set(profile2.interests.values_list('id', flat=True))
        common_interests = profile1_interests & profile2_interests
        
        if common_interests:
            interest_score = len(common_interests) * 15
            score += interest_score
            reasons.append(f"{len(common_interests)} shared interests")
        
        # Language compatibility (+20 points per common language)
        common_languages = set(profile1.languages_spoken) & set(profile2.languages_spoken)
        if common_languages:
            language_score = len(common_languages) * 20
            score += language_score
            reasons.append(f"Speaks {', '.join(common_languages)}")
        
        # Local expertise bonus (+40 points)
        if profile2.is_local_expert and profile2.is_available_to_help:
            score += 40
            reasons.append("Local expert available to help")
        
        # Helper availability (+25 points)
        elif profile2.is_available_to_help:
            score += 25
            reasons.append("Available to help")
        
        # High helper rating bonus (+30 points)
        if profile2.helper_rating >= 4.0:
            score += 30
            reasons.append(f"Highly rated helper ({profile2.helper_rating}/5.0)")
        
        # Recent activity bonus (+10 points)
        if profile2.user.last_login and profile2.user.last_login >= timezone.now() - timedelta(days=7):
            score += 10
            reasons.append("Active recently")
        
        return score, reasons
    
    @staticmethod
    def _calculate_travel_compatibility(profile1, profile2):
        """
        Calculate travel status compatibility bonus.
        Returns (bonus_score, reason_string)
        """
        status1 = profile1.travel_status
        status2 = profile2.travel_status
        
        # Perfect matches
        if status1 == 'traveling' and status2 == 'resident':
            return 35, "Local resident (can provide local insights)"
        
        if status1 == 'traveling' and status2 == 'expat':
            return 30, "Long-term expat (knows the area well)"
        
        if status1 == 'traveling' and status2 == 'traveling':
            # Check date overlap if available
            if (profile1.travel_start_date and profile1.travel_end_date and
                profile2.travel_start_date and profile2.travel_end_date):
                
                # Check for overlap
                if (profile1.travel_start_date <= profile2.travel_end_date and
                    profile1.travel_end_date >= profile2.travel_start_date):
                    return 40, "Fellow traveler with overlapping dates"
            
            return 25, "Fellow traveler"
        
        if status1 == 'resident' and status2 == 'traveling':
            return 20, "You can help this traveler"
        
        # Default bonus for any status match
        if status1 == status2:
            return 15, f"Same status ({status2.replace('_', ' ')})"
        
        return 0, None
    
    @staticmethod
    def get_travel_timeline_matches(user_profile):
        """
        Find people who will be in the same location during user's travel period.
        This is for future travel planning.
        """
        if not (user_profile.travel_start_date and user_profile.travel_end_date):
            return []
        
        # Find people from same country who will be in user's destination
        timeline_matches = Profile.objects.filter(
            home_country=user_profile.home_country,
            current_country=user_profile.current_country
        ).filter(
            Q(travel_start_date__lte=user_profile.travel_end_date) &
            Q(travel_end_date__gte=user_profile.travel_start_date)
        ).exclude(user=user_profile.user).select_related('user')
        
        return timeline_matches
    
    @staticmethod
    def get_emergency_network(user_profile, radius_km=50):
        """
        Find trusted countrymates who can help in emergencies.
        This could be expanded with GPS coordinates in the future.
        """
        emergency_contacts = Profile.objects.filter(
            home_country=user_profile.home_country,
            current_country=user_profile.current_country,
            current_city=user_profile.current_city,  # Same city for now
            is_available_to_help=True,
            user__is_active=True
        ).exclude(
            user=user_profile.user
        ).select_related('user').order_by('-helper_rating', '-help_requests_fulfilled')
        
        return emergency_contacts[:10]  # Top 10 potential helpers

class DiscoveryStats:
    """
    Helper class to generate statistics for discovery features.
    """
    
    @staticmethod
    def get_location_stats(user_profile):
        """
        Get statistics about countrymates in user's location.
        """
        countrymates = TravelerMatcher.find_countrymates_nearby(user_profile)
        
        stats = {
            'total_countrymates': countrymates.count(),
            'travelers': countrymates.filter(travel_status='traveling').count(),
            'residents': countrymates.filter(travel_status='resident').count(),
            'expats': countrymates.filter(travel_status='expat').count(),
            'local_experts': countrymates.filter(is_local_expert=True).count(),
            'available_helpers': countrymates.filter(is_available_to_help=True).count(),
        }
        
        return stats
    
    @staticmethod
    def get_global_network_size(home_country):
        """
        Get total network size for a country globally.
        """
        return Profile.objects.filter(home_country=home_country).count()
