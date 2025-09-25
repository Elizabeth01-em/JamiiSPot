#!/bin/bash

# Jamii Spot Messaging System Startup Script

echo "🚀 Starting Jamii Spot Messaging System..."

# Activate virtual environment
source venv/bin/activate

# Check if Redis is running (required for Celery and Channels)
if ! pgrep -x "redis-server" > /dev/null; then
    echo "⚠️  Redis is not running. Please start Redis server:"
    echo "   brew services start redis  (on macOS with Homebrew)"
    echo "   or"
    echo "   redis-server  (manual start)"
    echo ""
fi

# Apply any pending migrations
echo "📦 Applying database migrations..."
python manage.py migrate

# Start the Django server
echo "🌐 Starting Django development server..."
echo "📱 API will be available at: http://localhost:8000/api/"
echo "🔌 WebSocket endpoint: ws://localhost:8000/ws/notifications/?token=<jwt_token>"
echo ""
echo "📚 Available endpoints:"
echo "   - Conversations: /api/conversations/"
echo "   - Messages: /api/messages/"
echo "   - Communities: /api/communities/"
echo "   - Public Keys: /api/public-keys/"
echo "   - Encryption Keys: /api/encryption-keys/"
echo ""
echo "To start Celery worker (for background tasks), run in another terminal:"
echo "   source venv/bin/activate && celery -A jamii worker --loglevel=info"
echo ""
echo "Press Ctrl+C to stop the server"
echo "============================================"

python manage.py runserver 0.0.0.0:8000
