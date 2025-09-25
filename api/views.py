from django.contrib.auth.models import User
from .models import Profile, FriendRequest, Community, CommunityMembership,StoryPost, StoryItem, Conversation, ConversationParticipant
from .serializers import RegisterSerializer, ProfileSerializer, FriendRequestSerializer, CommunitySerializer,StoryPostSerializer
from rest_framework import generics, viewsets, permissions, serializers
from rest_framework.exceptions import ValidationError
from .permissions import IsOwnerOrReadOnly
from django.db import transaction, models
from .permissions import IsReceiver, IsCommunityAdminOrReadOnly
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
# Import the tasks module
from . import tasks
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)



# View for User Registration
class RegistrationAPIView(generics.CreateAPIView):
    from asgiref.sync import sync_to_async

    queryset = User.objects.all()
    # Anyone can register, so we allow any permission
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer

# ViewSet for Profile Management
class ProfileViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows user profiles to be viewed or edited.
    """
    # We join the 'user' table to our query to be more efficient
    queryset = Profile.objects.all().select_related('user')
    serializer_class = ProfileSerializer
    # We stack permissions: must be authenticated AND must be the owner to edit.
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    
    @action(detail=False, methods=['get', 'put', 'patch'], url_path='me')
    def me(self, request):
        """
        Get or update the current user's profile.
        GET /api/profiles/me/ - Get current user's profile
        PUT /api/profiles/me/ - Update current user's profile
        PATCH /api/profiles/me/ - Partially update current user's profile
        """
        try:
            # Try to get the user's profile
            profile = request.user.profile
        except Exception:
            # If profile doesn't exist, create one with default values
            profile = Profile.objects.create(
                user=request.user,
                home_country='',
                home_city='',
                current_country='',
                current_city=''
            )
        
        if request.method == 'GET':
            serializer = self.get_serializer(profile)
            return Response(serializer.data)
        elif request.method in ['PUT', 'PATCH']:
            partial = request.method == 'PATCH'
            serializer = self.get_serializer(profile, data=request.data, partial=partial)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class FriendRequestViewSet(viewsets.ModelViewSet):
    """
    API endpoint for handling friend requests.
    """
    serializer_class = FriendRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        This view should list friend requests sent or received by the user.
        """
        return FriendRequest.objects.filter(  # type: ignore
            models.Q(from_user=self.request.user) | 
            models.Q(to_user=self.request.user)
        )

    def perform_create(self, serializer):
        """
        Override to perform validation and automatically set from_user.
        Sends real-time notification when friend request is created.
        """
        to_user = serializer.validated_data['to_user']
        from_user = self.request.user
        
        if to_user == from_user:
            raise ValidationError("You cannot send a friend request to yourself.")

        # Check if they are already friends
        if from_user.profile.friends.filter(pk=to_user.profile.pk).exists():
             raise ValidationError("You are already friends.")

        # Check if a request already exists
        if FriendRequest.objects.filter(from_user=from_user, to_user=to_user).exists():  # type: ignore
             raise ValidationError("A friend request already exists.")
        
        # Save the friend request
        friend_request = serializer.save(from_user=self.request.user)
        
        # Send real-time notification to the recipient
        self.send_friend_request_notification(from_user, to_user, friend_request)
    
    def send_friend_request_notification(self, from_user, to_user, friend_request):
        """
        Send real-time notification when a friend request is sent
        """
        try:
            channel_layer = get_channel_layer()
            if channel_layer is not None:
                user_group = f"user_{to_user.id}"
                
                async_to_sync(channel_layer.group_send)(
                    user_group,
                    {
                        'type': 'send_notification',
                        'notification_type': 'friend_request_received',
                        'message': f'{from_user.username} sent you a friend request',
                        'data': {
                            'friend_request_id': friend_request.id,
                            'from_user_id': from_user.id,
                            'from_user_username': from_user.username,
                            'from_user_avatar': from_user.profile.avatar.url if from_user.profile.avatar else None,
                            'timestamp': friend_request.created_at.isoformat()
                        }
                    }
                )
            logger.info(f"Friend request notification sent to user {to_user.id} from {from_user.username}")
        except Exception as e:
            logger.error(f"Failed to send friend request notification: {e}")
    
    def send_friend_accepted_notification(self, from_user, to_user):
        """
        Send real-time notification when a friend request is accepted
        """
        try:
            channel_layer = get_channel_layer()
            if channel_layer is not None:
                user_group = f"user_{from_user.id}"
                
                async_to_sync(channel_layer.group_send)(
                    user_group,
                    {
                        'type': 'send_notification',
                        'notification_type': 'friend_request_accepted',
                        'message': f'{to_user.username} accepted your friend request!',
                        'data': {
                            'new_friend_id': to_user.id,
                            'new_friend_username': to_user.username,
                            'new_friend_avatar': to_user.profile.avatar.url if to_user.profile.avatar else None,
                            'timestamp': timezone.now().isoformat()
                        }
                    }
                )
            logger.info(f"Friend acceptance notification sent to user {from_user.id} from {to_user.username}")
        except Exception as e:
            logger.error(f"Failed to send friend acceptance notification: {e}")
        
    
    @action(detail=True, methods=['post'], permission_classes=[IsReceiver])
    def accept(self, request, pk=None):
        """Accept a friend request and send notifications"""
        friend_request = self.get_object()
        
        if friend_request.status != 'pending':
            return Response(
                {'error': 'This friend request has already been actioned.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update friend request status
        friend_request.status = 'accepted'
        friend_request.save()
        
        # Add users as friends
        from_user_profile = friend_request.from_user.profile
        to_user_profile = friend_request.to_user.profile
        
        from_user_profile.friends.add(to_user_profile)
        to_user_profile.friends.add(from_user_profile)
        
        # Send real-time notification to the requester
        self.send_friend_accepted_notification(
            friend_request.from_user, 
            friend_request.to_user
        )
        
        return Response({
            'status': 'Friend request accepted.',
            'friend_request_id': friend_request.id,
            'new_friend': {
                'id': friend_request.from_user.id,
                'username': friend_request.from_user.username,
                'avatar': friend_request.from_user.profile.avatar.url if friend_request.from_user.profile.avatar else None
            }
        })

    @action(detail=True, methods=['post'], permission_classes=[IsReceiver])
    def reject(self, request, pk=None):
        friend_request = self.get_object()
        if friend_request.status != 'pending':
            return Response(
                {'error': 'This friend request has already been actioned.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        friend_request.status = 'rejected'
        friend_request.save()
        return Response({'status': 'Friend request rejected.'})


class CommunityViewSet(viewsets.ModelViewSet):
    """
    API endpoint for creating and managing communities.
    """
    queryset = Community.objects.all()  # type: ignore
    serializer_class = CommunitySerializer
    # Secure this viewset with our custom permission
    permission_classes = [permissions.IsAuthenticated, IsCommunityAdminOrReadOnly]
    
    @transaction.atomic()  # Add back the parentheses for proper decorator usage
    def perform_create(self, serializer):  # type: ignore
        """
        Custom logic to make the creating user an admin of the new community
        and create a conversation for the community.
        """
        community = serializer.save(created_by=self.request.user)
        # Create the membership record making the creator an admin
        CommunityMembership.objects.create(  # type: ignore
            user=self.request.user,
            community=community,
            role='admin'
        )
        
        # Create a conversation for the community
        conversation = Conversation.objects.create(  # type: ignore
            conversation_type='community',
            community=community,
            name=f'{community.name} Chat',
            description=f'Main chat for {community.name}'
        )
        
        # Add the creator as a participant
        conversation.participants.add(self.request.user)
        ConversationParticipant.objects.create(  # type: ignore
            conversation=conversation,
            user=self.request.user,
            role='admin'
        )
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def join(self, request, pk=None):
        """
        Allow authenticated users to join a community.
        """
        community = self.get_object()
        
        # Check if user is already a member
        membership, created = CommunityMembership.objects.get_or_create(
            user=request.user,
            community=community,
            defaults={'role': 'member'}
        )
        
        if not created:
            return Response(
                {'message': 'You are already a member of this community.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Add user to the community conversation if it exists
        try:
            conversation = Conversation.objects.get(community=community)
            conversation.participants.add(request.user)
            ConversationParticipant.objects.get_or_create(
                conversation=conversation,
                user=request.user,
                defaults={'role': 'member'}
            )
        except Conversation.DoesNotExist:
            pass  # No conversation exists for this community
        
        serializer = self.get_serializer(community)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def leave(self, request, pk=None):
        """
        Allow members to leave a community.
        """
        community = self.get_object()
        
        # Check if user is a member
        try:
            membership = CommunityMembership.objects.get(
                user=request.user,
                community=community
            )
        except CommunityMembership.DoesNotExist:
            return Response(
                {'error': 'You are not a member of this community.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Prevent admins from leaving (they should delete the community instead)
        if membership.role == 'admin':
            return Response(
                {'error': 'Admins cannot leave communities. Please delete the community or transfer admin rights first.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Remove user from membership
        membership.delete()
        
        # Remove user from community conversation if it exists
        try:
            conversation = Conversation.objects.get(community=community)
            conversation.participants.remove(request.user)
            ConversationParticipant.objects.filter(
                conversation=conversation,
                user=request.user
            ).delete()
        except Conversation.DoesNotExist:
            pass  # No conversation exists for this community
        
        serializer = self.get_serializer(community)
        return Response(serializer.data)


# ViewSet for Story Posts
class StoryPostViewSet(viewsets.ModelViewSet):
    """
    API endpoint for creating and viewing stories.
    """
    queryset = StoryPost.objects.all().prefetch_related('items')  # type: ignore
    serializer_class = StoryPostSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def dispatch(self, request, *args, **kwargs):
        """
        Override dispatch to ensure this endpoint handles story requests correctly.
        """
        print(f"StoryPostViewSet.dispatch called with path: {request.path}")
        # Ensure this viewset handles the request
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        """
        Filter stories to show only those from friends and the current user.
        """
        user = self.request.user
        try:
            # Get friends of the current user
            friends = user.profile.friends.all() if hasattr(user, 'profile') else User.objects.none()
            # Include stories from friends and the user themselves
            return StoryPost.objects.filter(
                models.Q(sender__in=friends) | models.Q(sender=user)
            ).prefetch_related('items').order_by('-created_at')
        except Exception as e:
            logger.error(f"Error in get_queryset: {e}")
            # Return only the user's own stories as fallback
            return StoryPost.objects.filter(sender=user).prefetch_related('items').order_by('-created_at')

    def list(self, request, *args, **kwargs):
        """
        List all stories for the current user's feed.
        GET /api/stories/
        """
        print("StoryPostViewSet.list called")
        try:
            return super().list(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error in /api/stories/: {e}")
            return Response({"error": "Failed to retrieve stories"}, status=500)

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve a specific story.
        GET /api/stories/{id}/
        """
        print("StoryPostViewSet.retrieve called")
        try:
            return super().retrieve(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error in StoryPostViewSet.retrieve: {e}")
            return Response({"error": "Failed to retrieve story"}, status=500)

    @action(detail=False, methods=['get'])
    def me(self, request):
        """
        Get stories created by the current user.
        GET /api/stories/me/
        """
        print("StoryPostViewSet.me called")
        try:
            queryset = self.get_queryset().filter(sender=request.user)
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error in /api/stories/me/: {e}")
            return Response({"error": "Failed to retrieve stories"}, status=500)

    @action(detail=False, methods=['get'])
    def active_users(self, request):
        """
        Get users who have active (non-expired) stories.
        GET /api/stories/active-users/
        """
        print("StoryPostViewSet.active_users called")
        # Calculate the time 24 hours ago
        twenty_four_hours_ago = timezone.now() - timezone.timedelta(hours=24)
        
        # Get users who have stories created within the last 24 hours
        active_users = User.objects.filter(
            story_posts__created_at__gte=twenty_four_hours_ago
        ).distinct()
        
        # Serialize the user data
        user_data = []
        for user in active_users:
            has_active_stories = user.story_posts.filter(
                created_at__gte=twenty_four_hours_ago
            ).exists()
            
            # Safely get profile picture URL
            profile_picture = None
            try:
                if hasattr(user, 'profile') and user.profile.avatar:
                    profile_picture = user.profile.avatar.url
            except Exception as e:
                logger.error(f"Error getting avatar for user {user.id}: {e}")
                profile_picture = None
            
            user_data.append({
                'user_id': user.id,
                'username': user.username,
                'profile_picture': profile_picture,
                'has_active_stories': has_active_stories
            })
        
        return Response(user_data)

    def send_notification(self, user_id, notification_type, message, data=None):
        """
        Helper method to send WebSocket notifications to a specific user
        """
        try:
            channel_layer = get_channel_layer()
            if channel_layer is not None:
                user_group = f"user_{user_id}"
                
                async_to_sync(channel_layer.group_send)(
                    user_group,
                    {
                        'type': 'send_notification',
                        'message': message,
                        'notification_type': notification_type,
                        'data': data or {}
                    }
                )
            logger.info(f"Notification sent to user {user_id}: {message}")
        except Exception as e:
            logger.error(f"Failed to send notification to user {user_id}: {e}")

    # Override the create method for our async logic
    def create(self, request, *args, **kwargs):
        """
        Handles the creation of a story post.
        Accepts optional 'start_time' and 'end_time' for video trimming.
        Sends an initial "processing" notification via WebSocket.
        """
        print("StoryPostViewSet.create called")
        try:
            # (Your existing validation code for media_file, media_type, start/end time is good, keep it here)
            media_file = request.data.get('media_file')
            media_type = request.data.get('media_type')
            start_time_str = request.data.get('start_time')
            end_time_str = request.data.get('end_time')

            if not media_file or not media_type:
                return Response({"error": "Both 'media_file' and 'media_type' are required."}, status=status.HTTP_400_BAD_REQUEST)
            
            start_time, end_time = None, None
            if media_type == 'video' and start_time_str and end_time_str:
                 try:
                    start_time = float(start_time_str)
                    end_time = float(end_time_str)
                    if (end_time - start_time) > 30.5:
                         return Response({"error": "Duration cannot exceed 30 seconds."}, status=status.HTTP_400_BAD_REQUEST)
                 except (ValueError, TypeError):
                     return Response({"error": "Invalid time format."}, status=status.HTTP_400_BAD_REQUEST)

            # --- Database Creation ---
            story_post = StoryPost.objects.create(sender=request.user)  # type: ignore
            story_item = StoryItem.objects.create(  # type: ignore
                post=story_post, media_file=media_file, media_type=media_type, status='pending_upload'
            )
            
            # --- SEND INITIAL "PROCESSING" NOTIFICATION ---
            try:
                channel_layer = get_channel_layer()
                if channel_layer is not None:
                    user_group = f"user_{request.user.id}"
                    async_to_sync(channel_layer.group_send)(
                        user_group,
                        {
                            'type': 'send_notification',
                            'notification_type': 'story_upload_processing',
                            'message': f'Your {media_type} is now being processed.',
                            'data': {'story_id': story_post.id, 'status': 'processing'}
                        }
                    )
            except Exception as e:
                logger.error(f"Failed to send initial processing notification: {e}")
                
            # --- DISPATCH CELERY TASK ---
            # Pass user_id so the task knows who to notify on completion
            # Use getattr to bypass type checker issue with .delay attribute
            task = getattr(tasks, 'process_story_media')
            task.delay(story_item_id=story_item.id, user_id=request.user.id, start_time=start_time, end_time=end_time)

            serializer = self.get_serializer(story_post)
            return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
        except Exception as e:
            logger.error(f"Error in StoryPostViewSet.create: {e}")
            return Response({"error": "Failed to create story"}, status=500)
