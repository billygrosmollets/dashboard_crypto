#!/usr/bin/env python3
"""
WSGI Entry Point for Production
Gunicorn uses this file to start the Flask application
"""
import os
from app import create_app

# Create Flask app with production config
app = create_app('production')

# Start auto-refresh service when run by WSGI server (Gunicorn)
# This ensures background portfolio updates work in production
if __name__ != '__main__':
    # When imported by Gunicorn, start auto-refresh
    from services.auto_refresh import start_auto_refresh
    start_auto_refresh(app)
    print("✅ Auto-refresh service started (production mode)")

# Allow running directly for testing
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
