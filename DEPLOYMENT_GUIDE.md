# راهنمای استقرار روی سرویس‌های رایگان - Anti-Filter Bridge

## 🚀 گزینه‌های استقرار رایگان

### 1. Railway (توصیه شده) ⭐

**مزایا:**
- رایگان تا 500 ساعت در ماه
- پشتیبانی از Python
- دامنه رایگان
- SSL خودکار

**مراحل:**

#### 1.1 آماده‌سازی پروژه
```bash
# ایجاد فایل railway.json
cat > railway.json << EOF
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "python -m anti_filter_bridge.server --host 0.0.0.0 --port \$PORT",
    "healthcheckPath": "/status",
    "healthcheckTimeout": 100
  }
}
EOF
```

#### 1.2 ایجاد Procfile
```bash
cat > Procfile << EOF
web: python -m anti_filter_bridge.server --host 0.0.0.0 --port \$PORT
EOF
```

#### 1.3 تنظیم متغیرهای محیطی
```bash
# ایجاد فایل .env.production
cat > .env.production << EOF
APP_ENV=production
DEBUG=false
HOST=0.0.0.0
PORT=8443
SECRET_KEY=your-super-secure-secret-key-here
LOG_LEVEL=INFO
EOF
```

#### 1.4 استقرار
1. ثبت‌نام در [Railway](https://railway.app)
2. اتصال GitHub repository
3. انتخاب پروژه
4. تنظیم متغیرهای محیطی در dashboard
5. Deploy خودکار

---

### 2. Heroku

**مزایا:**
- رایگان (با محدودیت)
- پشتیبانی از Python
- Add-ons رایگان

**مراحل:**

#### 2.1 نصب Heroku CLI
```bash
# Windows
winget install Heroku.HerokuCLI

# یا دانلود از heroku.com
```

#### 2.2 ایجاد فایل‌های مورد نیاز
```bash
# runtime.txt
echo "python-3.11.0" > runtime.txt

# requirements.txt (قبلاً موجود است)
# Procfile (قبلاً ایجاد شد)
```

#### 2.3 استقرار
```bash
# ورود به Heroku
heroku login

# ایجاد اپلیکیشن
heroku create your-app-name

# تنظیم متغیرهای محیطی
heroku config:set APP_ENV=production
heroku config:set DEBUG=false
heroku config:set SECRET_KEY=your-secret-key

# استقرار
git add .
git commit -m "Deploy to Heroku"
git push heroku main
```

---

### 3. Render

**مزایا:**
- رایگان تا 750 ساعت
- SSL خودکار
- Auto-deploy از GitHub

**مراحل:**

#### 3.1 تنظیمات Render
1. ثبت‌نام در [Render](https://render.com)
2. اتصال GitHub repository
3. انتخاب "Web Service"
4. تنظیمات:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python -m anti_filter_bridge.server --host 0.0.0.0 --port $PORT`
   - **Environment:** Python 3

#### 3.2 متغیرهای محیطی
```
APP_ENV=production
DEBUG=false
HOST=0.0.0.0
PORT=10000
SECRET_KEY=your-secret-key
LOG_LEVEL=INFO
```

---

### 4. PythonAnywhere

**مزایا:**
- رایگان برای حساب‌های محدود
- پشتیبانی کامل از Python
- دامنه رایگان

**مراحل:**

#### 4.1 ایجاد حساب
1. ثبت‌نام در [PythonAnywhere](https://pythonanywhere.com)
2. انتخاب "Beginner" (رایگان)

#### 4.2 آپلود پروژه
```bash
# فشرده‌سازی پروژه
tar -czf anti-filter-bridge.tar.gz anti_filter_bridge/

# آپلود از طریق Files tab در PythonAnywhere
```

#### 4.3 تنظیم Web App
1. **Web tab** → **Add a new web app**
2. انتخاب **Manual configuration**
3. انتخاب **Python 3.11**
4. تنظیم **Source code** و **Working directory**

#### 4.4 فایل WSGI
```python
# /var/www/yourusername_pythonanywhere_com_wsgi.py
import sys
import os

# Add your project directory to the Python path
path = '/home/yourusername/anti_filter_bridge'
if path not in sys.path:
    sys.path.append(path)

# Import your application
from anti_filter_bridge.server import TunnelServer
import asyncio

# Create server instance
server = TunnelServer(host='0.0.0.0', port=8080)

# Run server
if __name__ == "__main__":
    asyncio.run(server.start())
```

---

### 5. Vercel (با محدودیت)

**مزایا:**
- رایگان
- سرعت بالا
- SSL خودکار

**محدودیت:**
- فقط برای API endpoints
- نیاز به تغییرات در کد

#### 5.1 ایجاد vercel.json
```json
{
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
```

#### 5.2 ایجاد api/server.py
```python
from anti_filter_bridge.server import TunnelServer
from vercel import Vercel

app = Vercel()

@app.route('/')
def home():
    return {"message": "Anti-Filter Bridge Server"}

@app.route('/ws')
def websocket():
    # WebSocket handling
    pass
```

---

## 🔧 تنظیمات پیش‌تولید

### 1. بهینه‌سازی برای استقرار

#### 1.1 فایل requirements.txt
```txt
# Core dependencies
websockets>=12.0
aiohttp>=3.8.0
asyncio>=3.4.3

# Security
cryptography>=41.0.0
python-dotenv>=1.0.0

# CLI
click>=8.0.0
rich>=13.0.0

# Configuration
pydantic>=2.0.0
pydantic-settings>=2.0.0

# Production
gunicorn>=21.0.0
uvicorn[standard]>=0.23.0
```

#### 1.2 فایل .env.production
```env
# Production Settings
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
```

### 2. اسکریپت استقرار خودکار

#### 2.1 deploy.sh
```bash
#!/bin/bash
# اسکریپت استقرار خودکار

echo "🚀 Deploying Anti-Filter Bridge..."

# بررسی وابستگی‌ها
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found"
    exit 1
fi

# نصب وابستگی‌ها
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# تولید گواهی SSL (اختیاری)
if [ ! -f "certs/cert.pem" ]; then
    echo "🔐 Generating SSL certificates..."
    python generate_certs.py
fi

# تست نصب
echo "🧪 Running tests..."
python test_installation.py

# شروع سرور
echo "🚀 Starting server..."
python -m anti_filter_bridge.server --host 0.0.0.0 --port $PORT
```

#### 2.2 deploy.bat (Windows)
```batch
@echo off
echo Deploying Anti-Filter Bridge...

REM نصب وابستگی‌ها
pip install -r requirements.txt

REM تولید گواهی SSL
if not exist "certs\cert.pem" (
    python generate_certs.py
)

REM تست نصب
python test_installation.py

REM شروع سرور
python -m anti_filter_bridge.server --host 0.0.0.0 --port %PORT%
```

---

## 🌐 تنظیم دامنه سفارشی

### 1. Railway
- در dashboard: **Settings** → **Domains**
- اضافه کردن دامنه سفارشی
- تنظیم DNS records

### 2. Heroku
```bash
# اضافه کردن دامنه
heroku domains:add yourdomain.com

# تنظیم DNS
# CNAME: www → your-app.herokuapp.com
# A Record: @ → IP address
```

### 3. Render
- **Settings** → **Custom Domains**
- اضافه کردن دامنه
- تنظیم DNS records

---

## 📊 مانیتورینگ و لاگ‌گیری

### 1. لاگ‌های سرور
```python
# در server.py
import logging
from datetime import datetime

# تنظیم لاگ‌گیری
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/server.log'),
        logging.StreamHandler()
    ]
)
```

### 2. مانیتورینگ سلامت
```python
# endpoint برای health check
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "0.1.0"
    }
```

---

## 🔒 امنیت در تولید

### 1. متغیرهای محیطی امن
```bash
# تولید secret key قوی
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 2. محدودیت‌های امنیتی
```python
# در server.py
RATE_LIMIT = 100  # درخواست در دقیقه
MAX_CONNECTIONS = 1000
TIMEOUT = 30  # ثانیه
```

### 3. فایروال
```bash
# فقط پورت‌های لازم را باز کنید
ufw allow 8443
ufw allow 22
ufw enable
```

---

## 🚨 عیب‌یابی

### 1. مشکلات رایج

#### خطای "Port already in use"
```bash
# پیدا کردن فرآیند
lsof -i :8443
# یا
netstat -tulpn | grep :8443

# کشتن فرآیند
kill -9 <PID>
```

#### خطای "Module not found"
```bash
# بررسی Python path
python -c "import sys; print(sys.path)"

# نصب مجدد
pip install -e .
```

#### خطای SSL
```bash
# تولید مجدد گواهی
python generate_certs.py

# یا استفاده از --insecure
python -m anti_filter_bridge.server --insecure
```

### 2. لاگ‌های مفید
```bash
# لاگ‌های سرور
tail -f logs/server.log

# لاگ‌های سیستم
journalctl -u your-service-name -f

# لاگ‌های Docker (اگر استفاده می‌کنید)
docker logs your-container-name
```

---

## 📈 بهینه‌سازی عملکرد

### 1. تنظیمات سرور
```python
# در server.py
class TunnelServer:
    def __init__(self):
        self.max_connections = 1000
        self.ping_interval = 30
        self.ping_timeout = 60
        self.max_message_size = 10 * 1024 * 1024  # 10MB
```

### 2. کش‌گذاری
```python
# کش DNS
import asyncio
from functools import lru_cache

@lru_cache(maxsize=1000)
async def resolve_dns(hostname):
    # DNS resolution with caching
    pass
```

### 3. فشرده‌سازی
```python
# در WebSocket connection
websockets.serve(
    handler,
    host, port,
    compression="deflate"  # Enable compression
)
```

---

## 🎯 توصیه نهایی

**برای شروع سریع:** Railway یا Render
**برای کنترل کامل:** VPS رایگان (Oracle Cloud, Google Cloud)
**برای مقیاس بالا:** Heroku یا AWS (با محدودیت رایگان)

---

**نکته مهم:** همیشه قبل از استقرار در تولید، در محیط تست آزمایش کنید!
