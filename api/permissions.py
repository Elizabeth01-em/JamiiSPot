from rest_framework import permissions
from api.models import CommunityMembership, ConversationParticipant

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the user associated with the profile.
        return obj.user == request.user
    
class IsReceiver(permissions.BasePermission):
    """
    Permission to only allow the receiver of a friend request to act on it.
    """
    def has_object_permission(self, request, view, obj):
        return obj.to_user == request.user

class IsCommunityAdminOrReadOnly(permissions.BasePermission):
    """
    Allow read-only access for anyone, but write access only to community admins.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to admins of the community.
        return CommunityMembership.objects.filter(
            user=request.user, 
            community=obj, 
            role='admin'
        ).exists()

class IsConversationParticipant(permissions.BasePermission):
    """
    Permission to only allow conversation participants to access messages.
    """
    def has_object_permission(self, request, view, obj):
        # Check if user is a participant in the conversation
        if hasattr(obj, 'conversation'):
            # This is a message
            conversation = obj.conversation
        else:
            # This is a conversation
            conversation = obj
        
        return conversation.participants.filter(id=request.user.id).exists()

class CanSendMessageInConversation(permissions.BasePermission):
    """
    Permission to check if user can send messages in a conversation.
    For channels, only admins/moderators can send messages.
    """
    def has_permission(self, request, view):
        if request.method not in ['POST', 'PUT', 'PATCH']:
            return True
        
        conversation_id = request.data.get('conversation')
        if not conversation_id:
            return False
        
        try:
            from .models import Conversation
            conversation = Conversation.objects.get(id=conversation_id)
            
            # Check if user is participant
            if not conversation.participants.filter(id=request.user.id).exists():
                return False
            
            # If it's a community conversation
            if conversation.conversation_type == 'community' and conversation.community:
                # If it's a channel, only admins/mods can post
                if conversation.community.is_channel:
                    return CommunityMembership.objects.filter(
                        user=request.user,
                        community=conversation.community,
                        role__in=['admin', 'moderator']
                    ).exists()
            
            return True
        except:
            return False

class IsMessageSender(permissions.BasePermission):
    """
    Permission to only allow message sender to edit/delete their messages.
    """
    def has_object_permission(self, request, view, obj):
        return obj.sender == request.user
