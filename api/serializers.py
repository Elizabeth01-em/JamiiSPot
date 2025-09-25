from django.contrib.auth.models import User
from rest_framework import serializers
from .models import (
    Profile, Interest, FriendRequest, Community, CommunityMembership, 
    StoryItem, StoryPost, Conversation, Message, MessageReadStatus, 
    UserEncryptionKey, ConversationParticipant
)


# This serializer is for read-only operations on the User model
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name']

# This is our main serializer for viewing and updating profiles
class ProfileSerializer(serializers.ModelSerializer):
    # We nest the UserSerializer to include user details in the profile response
    user = UserSerializer(read_only=True)
    # This is the read-only completeness score field we designed
    completeness_score = serializers.SerializerMethodField()
    # Allows for displaying interest names instead of just IDs
    interests = serializers.StringRelatedField(many=True, read_only=True)
    # Travel-specific computed fields
    is_traveling = serializers.SerializerMethodField()
    days_in_current_location = serializers.SerializerMethodField()
    travel_status_display = serializers.CharField(source='get_travel_status_display', read_only=True)

    class Meta:
        model = Profile
        # These are the fields that will be returned in the API response
        fields = [
            'user', 'bio', 'avatar', 'home_country', 'home_city',
            'current_country', 'current_city', 'interests', 'friends',
            'completeness_score', 
            # Travel-specific fields
            'travel_status', 'travel_status_display', 'is_traveling',
            'travel_start_date', 'travel_end_date', 'is_available_to_help',
            'languages_spoken', 'years_in_current_location', 'is_local_expert',
            'expertise_areas', 'helper_rating', 'help_requests_fulfilled',
            'days_in_current_location'
        ]
        read_only_fields = ['friends', 'helper_rating', 'help_requests_fulfilled'] # Friends should be managed via the friend request system

    def get_completeness_score(self, obj):
        """Calculates a profile completeness score as a percentage."""
        score = 0
        total_fields = 4  # bio, avatar, home_country, interests
        
        if obj.bio:
            score += 1
        if obj.avatar:
            score += 1
        if obj.home_country:
            score += 1
        if obj.interests.exists():
            score += 1
        
        return int((score / total_fields) * 100)
    
    def get_is_traveling(self, obj):
        """Check if user is currently traveling."""
        return obj.travel_status == 'traveling'
    
    def get_days_in_current_location(self, obj):
        """Calculate days in current location based on travel dates."""
        from django.utils import timezone
        from datetime import timedelta
        
        if obj.travel_start_date:
            # If user is traveling, calculate days since travel started
            if obj.travel_status == 'traveling':
                days_traveling = (timezone.now().date() - obj.travel_start_date).days
                return max(0, days_traveling)
            
        # For residents/expats, use years_in_current_location if available
        if obj.years_in_current_location:
            return obj.years_in_current_location * 365  # Approximate
            
        return None

# This serializer is ONLY for the registration endpoint
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password']
    
    def create(self, validated_data):
        """Handles the creation of a user and their empty profile."""
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        # We create an associated, empty profile upon registration
        # Provide default values for required fields
        Profile.objects.create(
            user=user,
            home_country='',
            home_city='',
            current_country='',
            current_city=''
        )
        return user
    
class FriendRequestSerializer(serializers.ModelSerializer):
    # We want to show the username of the sender, not just their ID
    from_user = serializers.StringRelatedField(read_only=True)
    # For creating a request, the client only needs to send the target user's ID
    to_user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = FriendRequest
        fields = ['id', 'from_user', 'to_user', 'status', 'created_at']
        read_only_fields = ['from_user', 'status', 'created_at']

class CommunitySerializer(serializers.ModelSerializer):
    # We add a read-only field to show the creator's username
    created_by = serializers.StringRelatedField(read_only=True)
    # We also add a simple member count for display on the frontend
    member_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Community
        fields = [
            'id', 'name', 'profile_image', 'description', 'created_by', 
            'created_at', 'is_channel', 'member_count'
        ]

    def get_member_count(self, obj):
        """Returns the number of members in the community."""
        return obj.members.count()
    
class StoryItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = StoryItem
        # Make status read-only, as it's controlled by the server process
        fields = ['id', 'media_file', 'media_type', 'duration_seconds', 'status']
        read_only_fields = ['status', 'duration_seconds']


class StoryPostSerializer(serializers.ModelSerializer):
    # We nest the item serializer to show the full story content
    items = StoryItemSerializer(many=True, read_only=True)
    # Show the sender's username
    sender = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = StoryPost
        fields = ['id', 'sender', 'created_at', 'items', 'viewers']

# User Encryption Key Serializer
class UserEncryptionKeySerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = UserEncryptionKey
        fields = ['user', 'public_key', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

# Conversation Participant Serializer
class ConversationParticipantSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = ConversationParticipant
        fields = [
            'user', 'role', 'joined_at', 'left_at', 'is_muted', 
            'last_seen_message', 'encrypted_conversation_key'
        ]
        read_only_fields = ['joined_at', 'encrypted_conversation_key']

# Message Serializer
class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    reply_to = serializers.PrimaryKeyRelatedField(read_only=True)
    reply_to_message = serializers.SerializerMethodField()
    is_read = serializers.SerializerMethodField()
    read_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Message
        fields = [
            'id', 'conversation', 'sender', 'message_type', 'encrypted_content',
            'media_file', 'timestamp', 'edited_at', 'is_deleted', 'deleted_at',
            'reply_to', 'reply_to_message', 'is_read', 'read_count'
        ]
        read_only_fields = [
            'sender', 'timestamp', 'edited_at', 'is_deleted', 'deleted_at',
            'reply_to_message', 'is_read', 'read_count'
        ]
    
    def get_reply_to_message(self, obj):
        """Get basic info about the replied-to message"""
        if obj.reply_to:
            return {
                'id': obj.reply_to.id,
                'sender': obj.reply_to.sender.username,
                'message_type': obj.reply_to.message_type,
                'timestamp': obj.reply_to.timestamp
            }
        return None
    
    def get_is_read(self, obj):
        """Check if current user has read this message"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.read_by.filter(id=request.user.id).exists()
        return False
    
    def get_read_count(self, obj):
        """Get count of users who have read this message"""
        return obj.read_by.count()

# Create Message Serializer (for sending new messages)
class CreateMessageSerializer(serializers.ModelSerializer):
    # For text messages, we'll accept plain text and encrypt it server-side
    content = serializers.CharField(write_only=True, required=False)
    reply_to = serializers.PrimaryKeyRelatedField(
        queryset=Message.objects.all(), 
        required=False, 
        allow_null=True
    )
    
    class Meta:
        model = Message
        fields = ['conversation', 'message_type', 'content', 'media_file', 'reply_to']
    
    def validate(self, attrs):
        """Ensure either content or media_file is provided based on message type"""
        message_type = attrs.get('message_type', 'text')
        content = attrs.get('content')
        media_file = attrs.get('media_file')
        
        if message_type == 'text' and not content:
            raise serializers.ValidationError("Content is required for text messages")
        elif message_type in ['image', 'video', 'audio', 'file'] and not media_file:
            raise serializers.ValidationError(f"Media file is required for {message_type} messages")
        
        return attrs

# Conversation Serializer
class ConversationSerializer(serializers.ModelSerializer):
    participants = UserSerializer(many=True, read_only=True)
    participant_details = ConversationParticipantSerializer(many=True, read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = [
            'id', 'conversation_type', 'participants', 'participant_details',
            'community', 'created_at', 'updated_at', 'name', 'description',
            'last_message', 'unread_count'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_last_message(self, obj):
        """Get the most recent message in this conversation"""
        last_message = obj.messages.filter(is_deleted=False).last()
        if last_message:
            return {
                'id': last_message.id,
                'sender': last_message.sender.username,
                'message_type': last_message.message_type,
                'timestamp': last_message.timestamp,
                # Don't include content for security - client will decrypt
            }
        return None
    
    def get_unread_count(self, obj):
        """Get count of unread messages for current user"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.messages.filter(
                is_deleted=False
            ).exclude(
                read_by=request.user
            ).exclude(
                sender=request.user  # Don't count own messages
            ).count()
        return 0

# Create Conversation Serializer
class CreateConversationSerializer(serializers.ModelSerializer):
    participant_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Conversation
        fields = ['conversation_type', 'name', 'description', 'participant_ids', 'community']
    
    def validate(self, attrs):
        """Validate conversation creation data"""
        conversation_type = attrs.get('conversation_type')
        participant_ids = attrs.get('participant_ids', [])
        community = attrs.get('community')
        
        if conversation_type == 'private' and len(participant_ids) != 1:
            raise serializers.ValidationError(
                "Private conversations must have exactly one other participant"
            )
        elif conversation_type == 'community' and not community:
            raise serializers.ValidationError(
                "Community conversations must specify a community"
            )
        elif conversation_type == 'group' and len(participant_ids) < 1:
            raise serializers.ValidationError(
                "Group conversations must have at least one other participant"
            )
        
        return attrs
