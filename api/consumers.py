# api/consumers.py
import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger(__name__)

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """
        Called when the websocket is handshaking as part of initial connection.
        """
        logger.info(f"WebSocket connection attempt from client: {self.scope.get('client')}")
        logger.info(f"User in scope: {self.scope.get('user')}")
        logger.info(f"User authenticated: {getattr(self.scope.get('user'), 'is_authenticated', False)}")
        
        # Accept the connection regardless of authentication for now
        # You can add authentication checks here later if needed
        await self.accept()
        
        # Send a welcome message
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Successfully connected to notifications',
            'user': str(self.scope['user']) if self.scope['user'] else 'Anonymous'
        }))
        
        # If user is authenticated, add them to their personal group
        user = self.scope.get('user')
        if user and hasattr(user, 'is_authenticated') and user.is_authenticated:
            self.user_group = f"user_{user.id}"
            await self.channel_layer.group_add(
                self.user_group,
                self.channel_name
            )
            logger.info(f"User {user.username} added to group {self.user_group}")
        else:
            self.user_group = None
            logger.info("Anonymous user connected")

    async def disconnect(self, close_code):
        """
        Called when the WebSocket closes for any reason.
        """
        logger.info(f"WebSocket disconnected with code: {close_code}")
        
        # Leave user group if they were in one
        if hasattr(self, 'user_group') and self.user_group:
            await self.channel_layer.group_discard(
                self.user_group,
                self.channel_name
            )
            logger.info(f"User removed from group {self.user_group}")

    async def receive(self, text_data):
        """
        Called when we get a text frame. Channels will JSON-decode the payload
        for us and pass it as the first argument.
        """
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type', 'message')
            message = text_data_json.get('message', '')
            
            logger.info(f"Received message: {text_data_json}")
            
            # Echo the message back to the client
            await self.send(text_data=json.dumps({
                'type': 'echo',
                'message': f'Echo: {message}',
                'original_type': message_type
            }))
            
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON received: {text_data}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Error processing message'
            }))

    # Handler for sending notifications to this user
    async def send_notification(self, event):
        """
        Called when someone sends a notification to the user's group
        """
        import datetime
        
        # Add timestamp if not provided
        timestamp = event.get('timestamp')
        if not timestamp:
            timestamp = datetime.datetime.utcnow().isoformat()
        
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'notification_type': event.get('notification_type', 'general'),
            'message': event['message'],
            'data': event.get('data', {}),
            'timestamp': timestamp
        }))
    
    # Handler for sending new messages
    async def send_message(self, event):
        """
        Called when a new message is sent to a conversation the user is part of
        """
        await self.send(text_data=json.dumps({
            'type': 'new_message',
            'message': event['message']
        }))
    
    # Handler for message deletion notifications
    async def message_deleted(self, event):
        """
        Called when a message is deleted
        """
        await self.send(text_data=json.dumps({
            'type': 'message_deleted',
            'message': event['message']
        }))
    
    # Handler for typing indicators
    async def typing_indicator(self, event):
        """
        Called when someone is typing in a conversation
        """
        await self.send(text_data=json.dumps({
            'type': 'typing_indicator',
            'conversation_id': event['conversation_id'],
            'user': event['user'],
            'is_typing': event['is_typing']
        }))
    
    # NEW: Travel-specific notification handlers
    async def countrymate_nearby(self, event):
        """
        Called when someone from the same country is discovered nearby
        """
        await self.send(text_data=json.dumps({
            'type': 'travel_notification',
            'notification_type': 'countrymate_nearby',
            'message': event['message'],
            'data': event.get('data', {})
        }))
    
    async def countrymate_traveling_nearby(self, event):
        """
        Called when a countrymate starts traveling in your area
        """
        await self.send(text_data=json.dumps({
            'type': 'travel_notification',
            'notification_type': 'countrymate_traveling_nearby',
            'message': event['message'],
            'data': event.get('data', {})
        }))
    
    async def travel_buddy_match(self, event):
        """
        Called when a potential travel buddy is found
        """
        await self.send(text_data=json.dumps({
            'type': 'travel_notification',
            'notification_type': 'travel_buddy_match',
            'message': event['message'],
            'data': event.get('data', {})
        }))
    
    async def local_expert_available(self, event):
        """
        Called when a local expert becomes available to help
        """
        await self.send(text_data=json.dumps({
            'type': 'travel_notification',
            'notification_type': 'local_expert_available',
            'message': event['message'],
            'data': event.get('data', {})
        }))
    
    async def location_search_performed(self, event):
        """
        Called when user performs a location-based search
        """
        await self.send(text_data=json.dumps({
            'type': 'discovery_activity',
            'notification_type': 'location_search_performed',
            'message': event['message'],
            'data': event.get('data', {})
        }))
    
    async def emergency_alert(self, event):
        """
        Called for emergency network notifications
        """
        await self.send(text_data=json.dumps({
            'type': 'emergency_notification',
            'notification_type': 'emergency_alert',
            'message': event['message'],
            'data': event.get('data', {}),
            'priority': 'high'
        }))
