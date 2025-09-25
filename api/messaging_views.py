# api/messaging_views.py

import base64
import logging
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Q, Max, Count
from django.utils import timezone
from rest_framework import viewsets, permissions, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .models import (
    Conversation, Message, MessageReadStatus, UserEncryptionKey, 
    ConversationParticipant, Community, CommunityMembership
)
from .serializers import (
    ConversationSerializer, CreateConversationSerializer, MessageSerializer,
    CreateMessageSerializer, UserEncryptionKeySerializer
)
from .permissions import (
    IsConversationParticipant, CanSendMessageInConversation, IsMessageSender
)
from .encryption import EncryptionManager, MessageEncryption

logger = logging.getLogger(__name__)

class UserEncryptionKeyViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user encryption keys.
    """
    serializer_class = UserEncryptionKeySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return UserEncryptionKey.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        # Generate key pair if not provided
        if 'public_key' not in serializer.validated_data:
            key_pair = EncryptionManager.generate_rsa_key_pair()
            # Store public key in database
            serializer.save(
                user=self.request.user,
                public_key=key_pair['public_key']
            )
            
            # Return private key to client (one time only!)
            return Response({
                'public_key': key_pair['public_key'],
                'private_key': key_pair['private_key'],
                'message': 'IMPORTANT: Save the private key securely. It will not be shown again!'
            }, status=status.HTTP_201_CREATED)
        else:
            serializer.save(user=self.request.user)

class ConversationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing conversations.
    """
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated, IsConversationParticipant]
    
    def get_queryset(self):
        """Return conversations where user is a participant"""
        return Conversation.objects.filter(
            participants=self.request.user
        ).prefetch_related('participants', 'messages', 'participant_details')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CreateConversationSerializer
        return ConversationSerializer
    
    @transaction.atomic
    def perform_create(self, serializer):
        """Create a new conversation"""
        validated_data = serializer.validated_data
        conversation_type = validated_data['conversation_type']
        participant_ids = validated_data.get('participant_ids', [])
        community = validated_data.get('community')
        
        # Create the conversation
        conversation = serializer.save()
        
        # Add the creator as a participant
        conversation.participants.add(self.request.user)
        
        # Create participant details for the creator
        ConversationParticipant.objects.create(
            conversation=conversation,
            user=self.request.user,
            role='admin' if conversation_type == 'group' else 'member'
        )
        
        if conversation_type == 'private':
            # Add the other participant
            other_user = User.objects.get(id=participant_ids[0])
            conversation.participants.add(other_user)
            ConversationParticipant.objects.create(
                conversation=conversation,
                user=other_user,
                role='member'
            )
        elif conversation_type == 'group':
            # Add all participants
            for user_id in participant_ids:
                user = User.objects.get(id=user_id)
                conversation.participants.add(user)
                ConversationParticipant.objects.create(
                    conversation=conversation,
                    user=user,
                    role='member'
                )
        elif conversation_type == 'community':
            # Add all community members
            community_members = community.members.all()
            for member in community_members:
                conversation.participants.add(member)
                # Get member's role in community
                membership = CommunityMembership.objects.get(user=member, community=community)
                ConversationParticipant.objects.create(
                    conversation=conversation,
                    user=member,
                    role=membership.role
                )
        
        # Generate shared encryption key for group/community conversations
        if conversation_type in ['group', 'community']:
            conversation_key = EncryptionManager.generate_aes_key()
            
            # Encrypt the conversation key for each participant
            for participant in conversation.participants.all():
                try:
                    user_public_key = participant.encryption_key.public_key
                    encrypted_key = EncryptionManager.encrypt_with_rsa(conversation_key, user_public_key)
                    
                    # Update participant's encrypted conversation key
                    participant_detail = ConversationParticipant.objects.get(
                        conversation=conversation, 
                        user=participant
                    )
                    participant_detail.encrypted_conversation_key = encrypted_key
                    participant_detail.save()
                except UserEncryptionKey.DoesNotExist:
                    logger.warning(f"User {participant.username} doesn't have encryption key")
    
    @action(detail=True, methods=['post'])
    def add_participants(self, request, pk=None):
        """Add participants to a group conversation"""
        conversation = self.get_object()
        
        if conversation.conversation_type != 'group':
            return Response(
                {'error': 'Can only add participants to group conversations'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user is admin
        participant = ConversationParticipant.objects.get(
            conversation=conversation, 
            user=request.user
        )
        if participant.role != 'admin':
            return Response(
                {'error': 'Only admins can add participants'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        user_ids = request.data.get('user_ids', [])
        added_users = []
        
        with transaction.atomic():
            for user_id in user_ids:
                try:
                    user = User.objects.get(id=user_id)
                    if not conversation.participants.filter(id=user_id).exists():
                        conversation.participants.add(user)
                        ConversationParticipant.objects.create(
                            conversation=conversation,
                            user=user,
                            role='member'
                        )
                        added_users.append(user.username)
                        
                        # Send system message
                        Message.objects.create(
                            conversation=conversation,
                            sender=request.user,
                            message_type='system',
                            encrypted_content=f'{user.username} was added to the group'
                        )
                except User.DoesNotExist:
                    continue
        
        return Response({
            'message': f'Added {len(added_users)} participants',
            'added_users': added_users
        })
    
    @action(detail=True, methods=['post'])
    def leave(self, request, pk=None):
        """Leave a conversation"""
        conversation = self.get_object()
        
        with transaction.atomic():
            # Update participant record
            participant = ConversationParticipant.objects.get(
                conversation=conversation,
                user=request.user
            )
            participant.left_at = timezone.now()
            participant.save()
            
            # Remove from participants (but keep history)
            # conversation.participants.remove(request.user)
            
            # Send system message
            Message.objects.create(
                conversation=conversation,
                sender=request.user,
                message_type='system',
                encrypted_content=f'{request.user.username} left the conversation'
            )
        
        return Response({'message': 'Left conversation successfully'})
    
    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        """Get messages for a conversation with pagination"""
        conversation = self.get_object()
        
        # Get messages with pagination
        page_size = int(request.query_params.get('page_size', 50))
        before_message_id = request.query_params.get('before')
        
        messages_qs = conversation.messages.filter(is_deleted=False).order_by('-timestamp')
        
        if before_message_id:
            try:
                before_message = Message.objects.get(id=before_message_id)
                messages_qs = messages_qs.filter(timestamp__lt=before_message.timestamp)
            except Message.DoesNotExist:
                pass
        
        messages = messages_qs[:page_size]
        serializer = MessageSerializer(messages, many=True, context={'request': request})
        
        return Response({
            'messages': serializer.data,
            'has_more': messages_qs.count() > page_size
        })

class MessageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing messages.
    """
    serializer_class = MessageSerializer
    permission_classes = [
        permissions.IsAuthenticated, 
        IsConversationParticipant,
        CanSendMessageInConversation
    ]
    
    def get_queryset(self):
        """Return messages from conversations where user is a participant"""
        user_conversations = Conversation.objects.filter(participants=self.request.user)
        return Message.objects.filter(
            conversation__in=user_conversations,
            is_deleted=False
        ).select_related('sender', 'conversation', 'reply_to')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CreateMessageSerializer
        return MessageSerializer
    
    @transaction.atomic
    def perform_create(self, serializer):
        """Create and encrypt a new message"""
        validated_data = serializer.validated_data
        conversation = validated_data['conversation']
        content = validated_data.get('content', '')
        message_type = validated_data.get('message_type', 'text')
        
        # Check if user can send messages (additional check)
        if conversation.conversation_type == 'community' and conversation.community:
            if conversation.community.is_channel:
                is_admin_or_mod = CommunityMembership.objects.filter(
                    user=self.request.user,
                    community=conversation.community,
                    role__in=['admin', 'moderator']
                ).exists()
                if not is_admin_or_mod:
                    raise permissions.PermissionDenied(
                        "Only admins and moderators can send messages in channels"
                    )
        
        message = None
        if message_type == 'text' and content:
            # Encrypt the message content
            try:
                if conversation.conversation_type == 'private':
                    # Get public keys for both participants
                    participants = conversation.participants.all()
                    sender_key = self.request.user.encryption_key.public_key
                    receiver_key = participants.exclude(id=self.request.user.id).first().encryption_key.public_key
                    
                    encrypted_data = MessageEncryption.encrypt_private_message(
                        content, sender_key, receiver_key
                    )
                else:
                    # Group/community message - use shared key
                    participant_detail = ConversationParticipant.objects.get(
                        conversation=conversation,
                        user=self.request.user
                    )
                    
                    if not participant_detail.encrypted_conversation_key:
                        raise Exception("No conversation key available")
                    
                    # Decrypt conversation key with user's private key (this would be done client-side)
                    # For now, we'll store a placeholder
                    encrypted_data = {
                        'encrypted_content': base64.b64encode(content.encode()).decode(),
                        'encrypted_keys': ''
                    }
                
                # Create the message
                message = serializer.save(
                    sender=self.request.user,
                    encrypted_content=encrypted_data['encrypted_content']
                )
                
            except Exception as e:
                logger.error(f"Message encryption failed: {e}")
                from rest_framework import serializers
                raise serializers.ValidationError("Failed to encrypt message")
        else:
            # Non-text message or system message
            message = serializer.save(sender=self.request.user)
        
        # Update conversation's updated_at timestamp
        conversation.updated_at = timezone.now()
        conversation.save()
        
        # Send real-time notification to all participants
        self.send_message_notification(message, conversation)
    
    def send_message_notification(self, message, conversation):
        """Send real-time message notification to all conversation participants"""
        try:
            channel_layer = get_channel_layer()
            
            # Send to all participants except sender
            for participant in conversation.participants.exclude(id=message.sender.id):
                user_group = f"user_{participant.id}"
                
                async_to_sync(channel_layer.group_send)(
                    user_group,
                    {
                        'type': 'send_message',
                        'message': {
                            'id': message.id,
                            'conversation_id': conversation.id,
                            'sender': message.sender.username,
                            'message_type': message.message_type,
                            'timestamp': message.timestamp.isoformat(),
                            'encrypted_content': message.encrypted_content,
                        }
                    }
                )
        except Exception as e:
            logger.error(f"Failed to send message notification: {e}")
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark a message as read"""
        message = self.get_object()
        
        # Create read status if it doesn't exist
        read_status, created = MessageReadStatus.objects.get_or_create(
            user=request.user,
            message=message
        )
        
        if created:
            # Also mark all previous messages in conversation as read
            previous_messages = Message.objects.filter(
                conversation=message.conversation,
                timestamp__lte=message.timestamp,
                is_deleted=False
            ).exclude(sender=request.user)
            
            for prev_message in previous_messages:
                MessageReadStatus.objects.get_or_create(
                    user=request.user,
                    message=prev_message
                )
        
        return Response({'message': 'Marked as read'})
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsMessageSender])
    def delete_message(self, request, pk=None):
        """Delete a message (soft delete)"""
        message = self.get_object()
        
        message.is_deleted = True
        message.deleted_at = timezone.now()
        message.save()
        
        # Send deletion notification
        try:
            channel_layer = get_channel_layer()
            conversation = message.conversation
            
            for participant in conversation.participants.all():
                user_group = f"user_{participant.id}"
                
                async_to_sync(channel_layer.group_send)(
                    user_group,
                    {
                        'type': 'message_deleted',
                        'message': {
                            'id': message.id,
                            'conversation_id': conversation.id,
                        }
                    }
                )
        except Exception as e:
            logger.error(f"Failed to send deletion notification: {e}")
        
        return Response({'message': 'Message deleted'})

# Get public keys for users (for encryption)
class PublicKeyAPIView(generics.ListAPIView):
    """
    Get public keys for users (for client-side encryption)
    """
    serializer_class = UserEncryptionKeySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user_ids = self.request.query_params.get('user_ids', '').split(',')
        user_ids = [uid for uid in user_ids if uid.isdigit()]
        
        return UserEncryptionKey.objects.filter(
            user__id__in=user_ids
        ).select_related('user')
