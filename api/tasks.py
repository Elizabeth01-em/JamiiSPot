# api/tasks.py

from celery import shared_task
import ffmpeg
import os
from django.conf import settings
import logging
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.utils import timezone

logger = logging.getLogger(__name__)

# This helper function is perfect.
def send_websocket_notification(user_id, notification_type, message, data=None):
    try:
        channel_layer = get_channel_layer()
        user_group = f"user_{user_id}"
        
        event_payload = {
            'type': 'send_notification',
            'notification_type': notification_type,
            'message': message,
            'data': data or {},
        }

        async_to_sync(channel_layer.group_send)(user_group, event_payload)
        logger.info(f"WebSocket notification sent to user {user_id}: {notification_type}")
    except Exception as e:
        logger.error(f"Failed to send WebSocket notification to user {user_id}: {e}")

def notify_friends_new_story(story_post):
    """
    Notify all friends when a user posts a new story
    """
    try:
        from .models import Profile
        
        sender_profile = story_post.sender.profile
        friends = sender_profile.friends.all()
        
        # Get the first story item for preview
        first_item = story_post.items.first()
        
        logger.info(f"Notifying {friends.count()} friends about new story from {story_post.sender.username}")
        
        for friend_profile in friends:
            try:
                # Send notification to each friend
                send_websocket_notification(
                    user_id=friend_profile.user.id,
                    notification_type='friend_new_story',
                    message=f'{story_post.sender.username} posted a new story',
                    data={
                        'story_id': story_post.id,
                        'sender_id': story_post.sender.id,
                        'sender_username': story_post.sender.username,
                        'sender_avatar': story_post.sender.profile.avatar.url if story_post.sender.profile.avatar else None,
                        'media_type': first_item.media_type if first_item else 'unknown',
                        'created_at': story_post.created_at.isoformat(),
                        'expires_at': (story_post.created_at + timezone.timedelta(hours=24)).isoformat() if story_post.created_at else None
                    }
                )
            except Exception as e:
                logger.error(f"Failed to notify friend {friend_profile.user.username} about story: {e}")
                
        logger.info(f"Story notifications sent successfully for story {story_post.id}")
    except Exception as e:
        logger.error(f"Failed to notify friends about new story {story_post.id}: {e}")

@shared_task
def process_story_media(story_item_id, user_id, start_time=None, end_time=None):
    from .models import StoryItem
    story_item = None
    
    try:
        story_item = StoryItem.objects.get(id=story_item_id)
        logger.info(f"[StoryProcess] Loaded StoryItem {story_item.id} for user {user_id}")

        input_path = story_item.media_file.path
        input_dir = os.path.dirname(input_path)
        filename, ext = os.path.splitext(os.path.basename(input_path))
        output_filename = f"{filename}_processed{ext}"
        output_path = os.path.join(input_dir, output_filename)
        final_duration = 5.0 

        logger.info(f"[StoryProcess] Processing {story_item.media_type}: {input_path}")

        if story_item.media_type == 'video':
            stream = ffmpeg.input(input_path)
            
            if start_time is not None and end_time is not None:
                stream = ffmpeg.trim(stream, start=start_time, end=end_time)
            else:
                probe = ffmpeg.probe(input_path)
                duration = float(probe['format']['duration'])
                if duration > 30.0:
                    stream = ffmpeg.trim(stream, start=0, end=30)
            
            stream = ffmpeg.output(stream, output_path).overwrite_output()
            # We add a capture_stderr=True to see ffmpeg's internal errors if any occur
            stdout, stderr = ffmpeg.run(stream, capture_stdout=True, capture_stderr=True)
            logger.info(f"FFmpeg stdout: {stdout.decode()}")
            logger.error(f"FFmpeg stderr: {stderr.decode()}")


            final_probe = ffmpeg.probe(output_path)
            final_duration = float(final_probe['format']['duration'])
        
        elif story_item.media_type == 'image':
            os.rename(input_path, output_path)
        
        logger.info("[StoryProcess] Media processing complete. Updating database.")
        new_model_path = os.path.join(os.path.dirname(story_item.media_file.name), output_filename)
        story_item.media_file.name = new_model_path
        story_item.status = 'complete'
        story_item.duration_seconds = final_duration
        story_item.save()
        
        # Send completion notification to the story creator
        send_websocket_notification(
            user_id=user_id,
            notification_type='story_processing_complete',
            message=f'Your {story_item.media_type} story is ready!',
            data={ 'story_id': story_item.post.id, 'status': 'complete' }
        )
        
        # Notify friends about the new story
        notify_friends_new_story(story_item.post)

        if os.path.exists(input_path):
             os.remove(input_path)

    # ============================================
    # ===== CRITICAL ERROR LOGGING (START) =======
    # ============================================
    except Exception as e:
        # We will now log the FULL traceback of the error
        logger.exception(f"FATAL ERROR processing story item {story_item_id}:")
        # ============================================
        # ===== CRITICAL ERROR LOGGING (END) =========
        # ============================================

        if story_item:
            story_item.status = 'error'
            story_item.save()

        send_websocket_notification(
            user_id=user_id,
            notification_type='story_processing_failed',
            message='An error occurred while processing your story.',
            data={ 'story_id': story_item.post.id, 'status': 'error', 'error_detail': str(e) }
        )