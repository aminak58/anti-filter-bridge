#!/usr/bin/env python3
"""
اسکریپت آماده‌سازی پروژه برای استقرار روی سرویس‌های رایگان
"""
import os
import sys
import shutil
from pathlib import Path

def create_production_files():
    """ایجاد فایل‌های مورد نیاز برای استقرار"""
    
    print("🚀 آماده‌سازی پروژه برای استقرار...")
    
    # 1. ایجاد Procfile
    print("📄 ایجاد Procfile...")
    with open("Procfile", "w") as f:
        f.write("web: python -m anti_filter_bridge.server --host 0.0.0.0 --port $PORT\n")
    
    # 2. ایجاد runtime.txt
    print("🐍 ایجاد runtime.txt...")
    with open("runtime.txt", "w") as f:
        f.write("python-3.11.0\n")
    
    # 3. ایجاد railway.json
    print("🚂 ایجاد railway.json...")
    railway_config = {
        "build": {
            "builder": "NIXPACKS"
        },
        "deploy": {
            "startCommand": "python -m anti_filter_bridge.server --host 0.0.0.0 --port $PORT",
            "healthcheckPath": "/status",
            "healthcheckTimeout": 100
        }
    }
    
    import json
    with open("railway.json", "w") as f:
        json.dump(railway_config, f, indent=2)
    
    # 4. ایجاد vercel.json
    print("▲ ایجاد vercel.json...")
    vercel_config = {
        "version": 2,
        "builds": [
            {
                "src": "api/server.py",
                "use": "@vercel/python"
            }
        ],
        "routes": [
            {
                "src": "/(.*)",
                "dest": "api/server.py"
            }
        ]
    }
    
    with open("vercel.json", "w") as f:
        json.dump(vercel_config, f, indent=2)
    
    # 5. ایجاد فایل .env.production
    print("⚙️ ایجاد .env.production...")
    env_production = """# Production Environment Variables
APP_ENV=production
DEBUG=false
HOST=0.0.0.0
PORT=8443

# Security (تغییر کنید!)
SECRET_KEY=your-very-secure-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/server.log

# SSL (برای سرویس‌های رایگان معمولاً خودکار است)
SSL_CERT_FILE=
SSL_KEY_FILE=

# Connection Settings
PING_INTERVAL=30
PING_TIMEOUT=60
MAX_MESSAGE_SIZE=10485760
MAX_CONNECTIONS=1000

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60
"""
    
    with open(".env.production", "w") as f:
        f.write(env_production)
    
    # 6. ایجاد پوشه api برای Vercel
    print("📁 ایجاد پوشه api...")
    api_dir = Path("api")
    api_dir.mkdir(exist_ok=True)
    
    # ایجاد api/server.py برای Vercel
    vercel_server = '''"""
Vercel serverless function for Anti-Filter Bridge
"""
from anti_filter_bridge.server import TunnelServer
import asyncio
import json

def handler(request):
    """Vercel handler function"""
    
    # CORS headers
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    }
    
    if request.method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': headers,
            'body': ''
        }
    
    if request.path == '/':
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'message': 'Anti-Filter Bridge Server',
                'status': 'running',
                'version': '0.1.0'
            })
        }
    
    if request.path == '/status':
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'status': 'healthy',
                'timestamp': '2024-01-01T00:00:00Z'
            })
        }
    
    return {
        'statusCode': 404,
        'headers': headers,
        'body': json.dumps({'error': 'Not found'})
    }
'''
    
    with open("api/server.py", "w") as f:
        f.write(vercel_server)
    
    # 7. ایجاد Dockerfile
    print("🐳 ایجاد Dockerfile...")
    dockerfile = """FROM python:3.11-slim

WORKDIR /app

# نصب وابستگی‌های سیستم
RUN apt-get update && apt-get install -y \\
    openssl \\
    && rm -rf /var/lib/apt/lists/*

# کپی فایل‌های پروژه
COPY . .

# نصب وابستگی‌های Python
RUN pip install --no-cache-dir -r requirements.txt

# ایجاد پوشه‌های لازم
RUN mkdir -p logs certs

# تولید گواهی SSL
RUN python generate_certs.py

# تنظیم متغیرهای محیطی
ENV PYTHONUNBUFFERED=1
ENV APP_ENV=production
ENV DEBUG=false

# باز کردن پورت
EXPOSE 8443

# دستور شروع
CMD ["python", "-m", "anti_filter_bridge.server", "--host", "0.0.0.0", "--port", "8443", "--certfile", "certs/cert.pem", "--keyfile", "certs/key.pem"]
"""
    
    with open("Dockerfile", "w") as f:
        f.write(dockerfile)
    
    # 8. ایجاد docker-compose.yml
    print("🐙 ایجاد docker-compose.yml...")
    docker_compose = """version: '3.8'

services:
  anti-filter-bridge:
    build: .
    ports:
      - "8443:8443"
    environment:
      - APP_ENV=production
      - DEBUG=false
      - HOST=0.0.0.0
      - PORT=8443
    volumes:
      - ./logs:/app/logs
      - ./certs:/app/certs
    restart: unless-stopped
"""
    
    with open("docker-compose.yml", "w") as f:
        f.write(docker_compose)
    
    # 9. ایجاد .dockerignore
    print("🚫 ایجاد .dockerignore...")
    dockerignore = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
env.bak/
venv.bak/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Git
.git/
.gitignore

# Logs
logs/
*.log

# Development
.env
.env.local
.env.development

# Test
tests/
test_*.py
*_test.py

# Documentation
docs/
*.md
!README.md
"""
    
    with open(".dockerignore", "w") as f:
        f.write(dockerignore)
    
    print("✅ فایل‌های استقرار ایجاد شدند!")

def create_deployment_scripts():
    """ایجاد اسکریپت‌های استقرار"""
    
    print("📜 ایجاد اسکریپت‌های استقرار...")
    
    # اسکریپت Railway
    railway_script = """#!/bin/bash
# اسکریپت استقرار Railway

echo "🚂 Deploying to Railway..."

# بررسی Railway CLI
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Installing..."
    npm install -g @railway/cli
fi

# ورود به Railway
railway login

# اتصال پروژه
railway link

# استقرار
railway up

echo "✅ Deployed to Railway!"
"""
    
    with open("deploy-railway.sh", "w") as f:
        f.write(railway_script)
    
    # اسکریپت Heroku
    heroku_script = """#!/bin/bash
# اسکریپت استقرار Heroku

echo "🟣 Deploying to Heroku..."

# بررسی Heroku CLI
if ! command -v heroku &> /dev/null; then
    echo "❌ Heroku CLI not found. Please install from heroku.com"
    exit 1
fi

# ورود به Heroku
heroku login

# ایجاد اپلیکیشن (اگر وجود ندارد)
if [ -z "$HEROKU_APP_NAME" ]; then
    echo "Creating Heroku app..."
    heroku create
else
    echo "Using existing app: $HEROKU_APP_NAME"
    heroku git:remote -a $HEROKU_APP_NAME
fi

# تنظیم متغیرهای محیطی
heroku config:set APP_ENV=production
heroku config:set DEBUG=false
heroku config:set SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")

# استقرار
git add .
git commit -m "Deploy to Heroku"
git push heroku main

echo "✅ Deployed to Heroku!"
"""
    
    with open("deploy-heroku.sh", "w") as f:
        f.write(heroku_script)
    
    # اسکریپت Docker
    docker_script = """#!/bin/bash
# اسکریپت استقرار Docker

echo "🐳 Building Docker image..."

# ساخت image
docker build -t anti-filter-bridge .

# اجرای container
docker run -d \\
  --name anti-filter-bridge \\
  -p 8443:8443 \\
  -e APP_ENV=production \\
  -e DEBUG=false \\
  anti-filter-bridge

echo "✅ Docker container started!"
echo "🌐 Server running on http://localhost:8443"
"""
    
    with open("deploy-docker.sh", "w") as f:
        f.write(docker_script)
    
    # اجرایی کردن اسکریپت‌ها
    for script in ["deploy-railway.sh", "deploy-heroku.sh", "deploy-docker.sh"]:
        try:
            os.chmod(script, 0o755)
        except:
            pass  # در Windows ممکن است کار نکند
    
    print("✅ اسکریپت‌های استقرار ایجاد شدند!")

def show_deployment_instructions():
    """نمایش دستورالعمل‌های استقرار"""
    
    print("\n" + "="*60)
    print("🎉 پروژه آماده استقرار است!")
    print("="*60)
    
    print("\n📋 گزینه‌های استقرار:")
    print("\n1. 🚂 Railway (توصیه شده):")
    print("   - ثبت‌نام در railway.app")
    print("   - اتصال GitHub repository")
    print("   - Deploy خودکار")
    
    print("\n2. 🟣 Heroku:")
    print("   - نصب Heroku CLI")
    print("   - اجرای: ./deploy-heroku.sh")
    
    print("\n3. ▲ Vercel:")
    print("   - ثبت‌نام در vercel.com")
    print("   - اتصال GitHub repository")
    print("   - Deploy خودکار")
    
    print("\n4. 🐳 Docker:")
    print("   - اجرای: ./deploy-docker.sh")
    print("   - یا: docker-compose up -d")
    
    print("\n5. 🌐 Render:")
    print("   - ثبت‌نام در render.com")
    print("   - اتصال GitHub repository")
    print("   - تنظیم Build Command: pip install -r requirements.txt")
    print("   - تنظیم Start Command: python -m anti_filter_bridge.server --host 0.0.0.0 --port $PORT")
    
    print("\n📚 برای جزئیات بیشتر:")
    print("   - مطالعه DEPLOYMENT_GUIDE.md")
    print("   - مطالعه QUICKSTART.md")
    
    print("\n⚠️ نکات مهم:")
    print("   - حتماً SECRET_KEY را تغییر دهید")
    print("   - در تولید از گواهی SSL معتبر استفاده کنید")
    print("   - لاگ‌ها را مانیتور کنید")

def main():
    """تابع اصلی"""
    
    print("🚀 Anti-Filter Bridge - Deployment Preparation")
    print("=" * 50)
    
    # بررسی وجود فایل‌های اصلی
    required_files = [
        "anti_filter_bridge/__init__.py",
        "anti_filter_bridge/server.py",
        "client.py",
        "requirements.txt"
    ]
    
    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print("❌ فایل‌های زیر یافت نشدند:")
        for file in missing_files:
            print(f"   - {file}")
        print("\nلطفاً ابتدا پروژه را کامل کنید.")
        return 1
    
    # ایجاد فایل‌های استقرار
    create_production_files()
    
    # ایجاد اسکریپت‌های استقرار
    create_deployment_scripts()
    
    # نمایش دستورالعمل‌ها
    show_deployment_instructions()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
