from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from django.db.models.manager import Manager

# Interest Model: Stores a list of possible interests.
class Interest(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self) -> str:
        return str(self.name)

# Profile Model: Extends Django's built-in User model.
class Profile(models.Model):
    # Add explicit type annotation for the objects manager to help type checkers
    from django.db.models import Manager
    objects: Manager = models.Manager()
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)  # type: ignore
    bio = models.TextField(blank=True, default='')
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    home_country = models.CharField(max_length=100, default='')
    home_city = models.CharField(max_length=100, default='')
    current_country = models.CharField(max_length=100, default='')
    current_city = models.CharField(max_length=100, default='')
    interests = models.ManyToManyField(Interest, blank=True)
    # The 'friends' relationship is implicitly handled by Django's User model if needed,
    # but a ManyToManyField here offers more profile-specific features.
    friends = models.ManyToManyField('self', blank=True)
    
    # TRAVEL-SPECIFIC FIELDS
    TRAVEL_STATUS_CHOICES = (
        ('traveling', 'Currently Traveling'),
        ('resident', 'Local Resident'),
        ('expat', 'Living Abroad Long-term'),
        ('returning', 'Returning Home'),
    )
    
    travel_status = models.CharField(
        max_length=20,
        choices=TRAVEL_STATUS_CHOICES,
        default='resident'
    )
    travel_start_date = models.DateField(null=True, blank=True)
    travel_end_date = models.DateField(null=True, blank=True)
    is_available_to_help = models.BooleanField(default=True)  # type: ignore # Help other travelers
    languages_spoken = models.JSONField(default=list)        # Languages user speaks
    years_in_current_location = models.PositiveIntegerField(null=True, blank=True)
    is_local_expert = models.BooleanField(default=False)  # type: ignore
    expertise_areas = models.JSONField(default=list)  # ['transportation', 'food', 'culture']
    helper_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    help_requests_fulfilled = models.PositiveIntegerField(default=0)  # type: ignore

    def __str__(self) -> str:
        return str(self.user.username)  # type: ignore

# Friend Request Model
class FriendRequest(models.Model):
    # Add explicit type annotation for the objects manager to help type checkers
    from django.db.models import Manager
    objects: Manager = models.Manager()
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    )
    
    from_user = models.ForeignKey(User, related_name='sent_friend_requests', on_delete=models.CASCADE)  # type: ignore
    to_user = models.ForeignKey(User, related_name='received_friend_requests', on_delete=models.CASCADE)  # type: ignore
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    
    class Meta:
        unique_together = ('from_user', 'to_user')
    
    def __str__(self) -> str:
        return f"{self.from_user.username} -> {self.to_user.username} ({self.status})"  # type: ignore

# Story Post Model
class StoryPost(models.Model):
    # Add explicit type annotation for the objects manager to help type checkers
    from django.db.models import Manager
    objects: Manager = models.Manager()
    
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='story_posts')  # type: ignore
    created_at = models.DateTimeField(auto_now_add=True)
    viewers = models.ManyToManyField(User, related_name='viewed_story_posts', blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self) -> str:
        return f"Story by {self.sender.username} at {self.created_at}"  # type: ignore

# Story Item Model
class StoryItem(models.Model):
    # Add explicit type annotation for the objects manager to help type checkers
    from django.db.models import Manager
    objects: Manager = models.Manager()
    
    MEDIA_TYPE_CHOICES = (
        ('image', 'Image'),
        ('video', 'Video'),
    )
    
    post = models.ForeignKey(StoryPost, on_delete=models.CASCADE, related_name='items')  # type: ignore
    media_file = models.FileField(upload_to='story_media/')
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPE_CHOICES)
    duration_seconds = models.DecimalField(max_digits=5, decimal_places=2, default=5.0)
    status = models.CharField(max_length=20, default='pending_upload')
    
    def __str__(self) -> str:
        return f"{self.media_type} for {self.post}"

# Community Model: The main group or community.
class Community(models.Model):
    # Add explicit type annotation for the objects manager to help type checkers
    from django.db.models import Manager
    objects: Manager = models.Manager()
    
    name = models.CharField(max_length=150, unique=True)
    profile_image = models.ImageField(upload_to='community_profiles/', null=True, blank=True)
    description = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='founded_communities')  # type: ignore
    created_at = models.DateTimeField(auto_now_add=True)
    # This links Users to the community VIA the CommunityMembership model.
    members = models.ManyToManyField(User, through='CommunityMembership', related_name='communities')
    is_channel = models.BooleanField(default=False)  # type: ignore # True = only admins/mods can post

    def __str__(self) -> str:
        return str(self.name)

# CommunityMembership "Through" Model: Defines the relationship between a User and a Community.
class CommunityMembership(models.Model):
    # Add explicit type annotation for the objects manager to help type checkers
    from django.db.models import Manager
    objects: Manager = models.Manager()
    
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('moderator', 'Moderator'),
        ('member', 'Member'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)  # type: ignore
    community = models.ForeignKey(Community, on_delete=models.CASCADE)  # type: ignore
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    joined_at = models.DateTimeField(auto_now_add=True)

    # Ensures a user can only have one role in a specific community.
    class Meta:
        unique_together = ('user', 'community')

    def __str__(self) -> str:
        return f'{self.user.username} in {self.community.name} as {self.get_role_display()}'  # type: ignore
    
    def get_role_display(self) -> str:  # type: ignore
        role_dict = dict(self.ROLE_CHOICES)
        return role_dict.get(str(self.role), str(self.role))

# Conversation Model: Groups messages between users or in communities
class Conversation(models.Model):
    # Add explicit type annotation for the objects manager to help type checkers
    from django.db.models import Manager
    objects: Manager = models.Manager()
    
    CONVERSATION_TYPES = (
        ('private', 'Private'),
        ('group', 'Group'),
        ('community', 'Community'),
    )
    
    conversation_type = models.CharField(max_length=20, choices=CONVERSATION_TYPES)
    participants = models.ManyToManyField(User, related_name='conversations')
    community = models.OneToOneField(Community, on_delete=models.CASCADE, null=True, blank=True, related_name='conversation')  # type: ignore
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # For group conversations
    name = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self) -> str:
        if self.conversation_type == 'private':
            participants = list(self.participants.all())  # type: ignore
            if len(participants) >= 2:
                return f'Private: {participants[0].username} & {participants[1].username}'  # type: ignore
            return f'Private conversation {self.id}'  # type: ignore
        elif self.conversation_type == 'community':
            return f'Community: {self.community.name if self.community else "Unknown"}'  # type: ignore
        else:
            return f'Group: {self.name or f"Group {self.id}"}'  # type: ignore

# Message Model: Enhanced for different conversation types with E2E encryption
class Message(models.Model):
    # Add explicit type annotation for the objects manager to help type checkers
    from django.db.models import Manager
    objects: Manager = models.Manager()
    
    MESSAGE_TYPES = (
        ('text', 'Text'),
        ('image', 'Image'),
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('file', 'File'),
        ('system', 'System'),  # For system messages like "User joined", etc.
    )
    
    conversation = models.ForeignKey(Conversation, related_name='messages', on_delete=models.CASCADE)  # type: ignore
    sender = models.ForeignKey(User, related_name='sent_messages', on_delete=models.CASCADE)  # type: ignore
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPES, default='text')
    
    # Encrypted content (for text messages)
    encrypted_content = models.TextField(blank=True)
    
    # For media messages
    media_file = models.FileField(upload_to='message_media/', null=True, blank=True)
    
    # Message metadata
    timestamp = models.DateTimeField(auto_now_add=True)
    edited_at = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)  # type: ignore
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    # Reply functionality
    reply_to = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='replies')  # type: ignore
    
    # Message status tracking
    delivered_to = models.ManyToManyField(User, related_name='delivered_messages', blank=True)
    read_by = models.ManyToManyField(User, through='MessageReadStatus', related_name='read_messages')

    class Meta:
        ordering = ['timestamp']

    def __str__(self) -> str:
        return f'From {self.sender.username} in {self.conversation} at {self.timestamp:%Y-%m-%d %H:%M}'  # type: ignore
    
    @property
    def is_system_message(self):
        return self.message_type == 'system'

# Message Read Status: Tracks when users read messages
class MessageReadStatus(models.Model):
    # Add explicit type annotation for the objects manager to help type checkers
    from django.db.models import Manager
    objects: Manager = models.Manager()
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # type: ignore
    message = models.ForeignKey(Message, on_delete=models.CASCADE)  # type: ignore
    read_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'message')
    
    def __str__(self) -> str:
        return f'{self.user.username} read message {self.message.id} at {self.read_at}'  # type: ignore

# User Encryption Keys: Stores public keys for E2E encryption
class UserEncryptionKey(models.Model):
    # Add explicit type annotation for the objects manager to help type checkers
    from django.db.models import Manager
    objects: Manager = models.Manager()
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='encryption_key')  # type: ignore
    public_key = models.TextField()  # RSA public key in PEM format
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self) -> str:
        return f'Encryption key for {self.user.username}'  # type: ignore

# Conversation Participants: Enhanced through model for conversation membership
class ConversationParticipant(models.Model):
    # Add explicit type annotation for the objects manager to help type checkers
    from django.db.models import Manager
    objects: Manager = models.Manager()
    
    PARTICIPANT_ROLES = (
        ('member', 'Member'),
        ('admin', 'Admin'),
        ('moderator', 'Moderator'),
    )
    
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='participant_details')  # type: ignore
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # type: ignore
    role = models.CharField(max_length=20, choices=PARTICIPANT_ROLES, default='member')
    joined_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(null=True, blank=True)
    is_muted = models.BooleanField(default=False)  # type: ignore
    last_seen_message = models.ForeignKey(Message, null=True, blank=True, on_delete=models.SET_NULL)  # type: ignore
    
    # Encryption key for this specific conversation (for group key exchange)
    encrypted_conversation_key = models.TextField(blank=True)  # Conversation key encrypted with user's public key
    
    class Meta:
        unique_together = ('conversation', 'user')
    
    def __str__(self) -> str:
        return f'{self.user.username} in {self.conversation} as {self.role}'  # type: ignore