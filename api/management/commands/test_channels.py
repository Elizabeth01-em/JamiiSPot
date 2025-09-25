# api/management/commands/test_channels.py
from django.core.management.base import BaseCommand
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import time

class Command(BaseCommand):
    help = 'Tests the Django Channels layer connection to Redis'

    def handle(self, *args, **options):
        channel_layer = get_channel_layer()
        self.stdout.write(self.style.SUCCESS('Got default channel layer...'))
        
        # The test message payload
        message = {"type": "send_notification", "message": "This is a test!"}
        
        self.stdout.write('Attempting to send a test message...')
        
        try:
            # Use async_to_sync to call the async method from a sync context
            start_time = time.time()
            async_to_sync(channel_layer.group_send)("test_group", message)
            end_time = time.time()

            self.stdout.write(self.style.SUCCESS(f'Successfully sent message to Redis! Round trip took {end_time - start_time:.4f} seconds.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to send message to Redis. Error: {e}'))