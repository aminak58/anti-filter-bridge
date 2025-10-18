# 🚀 Deploy to PythonAnywhere - 100% Free

## Step 1: Create PythonAnywhere Account
1. Go to [pythonanywhere.com](https://pythonanywhere.com)
2. Click "Sign up"
3. Choose "Beginner" account (free)
4. No credit card required

## Step 2: Upload Code
1. In PythonAnywhere Dashboard, go to "Files" tab
2. Create a new directory: `anti_filter_bridge`
3. Upload all project files to this directory

## Step 3: Install Dependencies
1. Go to "Consoles" tab
2. Start a new Bash console
3. Run:
```bash
cd anti_filter_bridge
pip3.10 install --user -r requirements.txt
```

## Step 4: Create Web App
1. Go to "Web" tab
2. Click "Add a new web app"
3. Choose "Manual configuration"
4. Select Python 3.10
5. Click "Next"

## Step 5: Configure WSGI
1. In the WSGI configuration file, replace the content with:
```python
import sys
import os

# Add your project directory to the Python path
path = '/home/yourusername/anti_filter_bridge'
if path not in sys.path:
    sys.path.append(path)

# Import your application
from anti_filter_bridge.server import main
import asyncio

# Create the application
def application(environ, start_response):
    # This is a simple HTTP response for health checks
    if environ['PATH_INFO'] == '/status':
        status = '200 OK'
        headers = [('Content-type', 'application/json')]
        start_response(status, headers)
        return [b'{"status": "healthy", "message": "Anti-Filter Bridge Server is running", "version": "0.1.0"}']
    else:
        status = '200 OK'
        headers = [('Content-type', 'text/html')]
        start_response(status, headers)
        return [b'<h1>Anti-Filter Bridge Server</h1><p>WebSocket endpoint: wss://yourusername.pythonanywhere.com/ws</p>']
```

## Step 6: Configure WebSocket
1. In the Web app configuration, enable WebSocket
2. Set the WebSocket URL to: `/ws`

## Step 7: Test
1. Your app will be available at: `https://yourusername.pythonanywhere.com`
2. Test health check: `https://yourusername.pythonanywhere.com/status`

## Features
- ✅ 100% free forever
- ✅ No credit card required
- ✅ WebSocket support
- ✅ Custom domain support
- ✅ SSH access
- ⚠️ Limited CPU seconds (100 per day)
- ⚠️ Limited bandwidth
