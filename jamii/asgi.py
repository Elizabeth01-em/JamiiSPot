# jamii/asgi.py

# ============================================
# SECTION 1: Standard Library Imports
# ============================================
import os
import django
from django.core.asgi import get_asgi_application

# ============================================
# SECTION 2: Django Setup
# This is the most critical part. It must run before any of your
# own application modules are imported.
# ============================================
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jamii.settings')
django.setup()

# ============================================
# SECTION 3: Application and Library Imports
# Now that Django is set up, we can safely import our modules.
# ============================================
from channels.routing import ProtocolTypeRouter, URLRouter
from api.middleware import JwtAuthMiddleware
import api.routing

# The application routing configuration.
application = ProtocolTypeRouter({
    # The native ASGI application for HTTP requests. It is async-safe.
    "http": get_asgi_application(),

    # WebSocket routing with our custom authentication middleware.
    "websocket": JwtAuthMiddleware(
        URLRouter(
            api.routing.websocket_urlpatterns
        )
    ),
})