#!/usr/bin/env python
"""
Jamii Spot Backend Setup Verification Script

This script verifies that all components are working correctly:
1. Redis connection
2. Django settings
3. ASGI application
4. WebSocket routing

Usage:
    python verify_setup.py
"""

import os
import sys
import django
from pathlib import Path

# Add the project directory to Python path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jamii.settings')
django.setup()

def check_redis():
    """Check Redis connection"""
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        print("✅ Redis connection: SUCCESS")
        return True
    except Exception as e:
        print(f"❌ Redis connection: FAILED - {e}")
        return False

def check_channel_layers():
    """Check channel layer configuration"""
    try:
        from channels.layers import get_channel_layer
        channel_layer = get_channel_layer()
        print(f"✅ Channel layer: {channel_layer.__class__.__name__}")
        return True
    except Exception as e:
        print(f"❌ Channel layer: FAILED - {e}")
        return False

def check_asgi_app():
    """Check ASGI application"""
    try:
        from jamii.asgi import application
        print("✅ ASGI application: SUCCESS")
        return True
    except Exception as e:
        print(f"❌ ASGI application: FAILED - {e}")
        return False

def check_websocket_routing():
    """Check WebSocket routing"""
    try:
        from api.routing import websocket_urlpatterns
        print(f"✅ WebSocket routing: {len(websocket_urlpatterns)} patterns found")
        for pattern in websocket_urlpatterns:
            print(f"   - {pattern.pattern}")
        return True
    except Exception as e:
        print(f"❌ WebSocket routing: FAILED - {e}")
        return False

def check_consumers():
    """Check WebSocket consumers"""
    try:
        from api.consumers import NotificationConsumer
        print("✅ WebSocket consumers: SUCCESS")
        return True
    except Exception as e:
        print(f"❌ WebSocket consumers: FAILED - {e}")
        return False

def check_jwt_middleware():
    """Check JWT middleware"""
    try:
        from api.middleware import JwtAuthMiddleware
        print("✅ JWT middleware: SUCCESS")
        return True
    except Exception as e:
        print(f"❌ JWT middleware: FAILED - {e}")
        return False

def check_database():
    """Check database connection"""
    try:
        from django.db import connection
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        print("✅ Database connection: SUCCESS")
        return True
    except Exception as e:
        print(f"❌ Database connection: FAILED - {e}")
        return False

def main():
    """Run all checks"""
    print("🔍 Jamii Spot Backend Setup Verification")
    print("=" * 50)
    
    checks = [
        ("Redis Connection", check_redis),
        ("Database Connection", check_database),
        ("Channel Layers", check_channel_layers),
        ("ASGI Application", check_asgi_app),
        ("WebSocket Routing", check_websocket_routing),
        ("WebSocket Consumers", check_consumers),
        ("JWT Middleware", check_jwt_middleware),
    ]
    
    results = []
    for name, check_func in checks:
        print(f"\n📋 Checking {name}...")
        success = check_func()
        results.append((name, success))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 50)
    
    passed = 0
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {name}")
        if success:
            passed += 1
    
    print(f"\nResults: {passed}/{len(results)} checks passed")
    
    if passed == len(results):
        print("\n🎉 All checks passed! Your setup is ready for WebSocket testing.")
        print("\n🚀 To start the server with WebSocket support, run:")
        print("   python -m daphne -b 0.0.0.0 -p 8000 jamii.asgi:application")
        print("\n🔌 WebSocket URL:")
        print("   ws://localhost:8000/ws/notifications/?token=<your_jwt_token>")
    else:
        print(f"\n⚠️  {len(results) - passed} checks failed. Please fix the issues above.")
    
    return passed == len(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
