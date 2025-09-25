#!/usr/bin/env python
"""
Start script for Jamii Spot Backend with WebSocket support.

This script starts the Django Channels server using Daphne ASGI server,
which supports both HTTP and WebSocket connections.

Usage:
    python start_server.py

The server will run on http://localhost:8000 with WebSocket support at:
    ws://localhost:8000/ws/notifications/?token=<your_jwt_token>
"""

import os
import sys
import subprocess

def main():
    print("🚀 Starting Jamii Spot Backend with WebSocket support...")
    print("📡 Server will be available at: http://localhost:8000")
    print("🔌 WebSocket endpoint: ws://localhost:8000/ws/notifications/?token=<your_jwt_token>")
    print("⏹️  Press Ctrl+C to stop the server")
    print("-" * 80)
    
    try:
        # Start the ASGI server with Daphne
        subprocess.run([
            sys.executable, "-m", "daphne", 
            "-b", "0.0.0.0", 
            "-p", "8000", 
            "jamii.asgi:application"
        ], check=True)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error starting server: {e}")
        print("\n💡 Make sure you have installed the required packages:")
        print("   pip install daphne channels")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()
