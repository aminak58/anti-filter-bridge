# راهنمای استقرار روی Railway - Anti-Filter Bridge

## 🚂 Railway (ساده‌ترین و سریع‌ترین روش)

### چرا Railway؟
- ✅ **رایگان** تا 500 ساعت در ماه
- ✅ **SSL خودکار** و دامنه رایگان
- ✅ **Deploy خودکار** از GitHub
- ✅ **پشتیبانی کامل** از Python
- ✅ **تنظیمات ساده** بدون پیچیدگی

---

## ⚡ استقرار در 5 دقیقه

### مرحله 1: آماده‌سازی پروژه
```bash
# اجرای اسکریپت آماده‌سازی
python prepare_deployment.py
```

### مرحله 2: آپلود به GitHub
```bash
# اگر هنوز repository ندارید
git init
git add .
git commit -m "Initial commit"

# ایجاد repository در GitHub
# سپس:
git remote add origin https://github.com/yourusername/anti-filter-bridge.git
git push -u origin main
```

### مرحله 3: استقرار روی Railway

#### 3.1 ثبت‌نام و ورود
1. برو به [railway.app](https://railway.app)
2. کلیک روی **"Login"**
3. انتخاب **"Login with GitHub"**
4. اجازه دسترسی به repository

#### 3.2 ایجاد پروژه جدید
1. کلیک روی **"New Project"**
2. انتخاب **"Deploy from GitHub repo"**
3. انتخاب repository شما: `anti-filter-bridge`
4. کلیک روی **"Deploy Now"**

#### 3.3 تنظیم متغیرهای محیطی
1. در dashboard پروژه، برو به **"Variables"**
2. اضافه کردن متغیرهای زیر:

```
APP_ENV=production
DEBUG=false
HOST=0.0.0.0
PORT=8443
SECRET_KEY=your-very-secure-secret-key-here
LOG_LEVEL=INFO
```

#### 3.4 تنظیم دامنه (اختیاری)
1. برو به **"Settings"** → **"Domains"**
2. کلیک روی **"Generate Domain"** برای دامنه رایگان
3. یا اضافه کردن دامنه سفارشی خود

---

## 🔧 تنظیمات پیشرفته

### 1. تنظیم Health Check
Railway به طور خودکار health check انجام می‌دهد. endpoint `/status` در کد موجود است.

### 2. تنظیم Logs
```bash
# مشاهده لاگ‌ها در Railway dashboard
# یا از طریق Railway CLI:
railway logs
```

### 3. تنظیم Environment Variables
```bash
# از طریق Railway CLI
railway variables set SECRET_KEY=your-new-secret-key
railway variables set LOG_LEVEL=DEBUG
```

---

## 🚀 دستورات مفید Railway

### نصب Railway CLI
```bash
# Windows
npm install -g @railway/cli

# macOS
brew install railway

# Linux
curl -fsSL https://railway.app/install.sh | sh
```

### دستورات مفید
```bash
# ورود
railway login

# اتصال به پروژه
railway link

# مشاهده لاگ‌ها
railway logs

# تنظیم متغیرها
railway variables set KEY=value

# استقرار مجدد
railway up

# مشاهده وضعیت
railway status
```

---

## 🌐 دسترسی به سرور

### URL سرور
پس از استقرار، Railway یک URL رایگان به شما می‌دهد:
```
https://your-app-name.railway.app
```

### تست اتصال
```bash
# تست health check
curl https://your-app-name.railway.app/status

# تست WebSocket (از کلاینت)
python client.py --server wss://your-app-name.railway.app --local-port 1080
```

---

## 🔒 امنیت

### 1. تغییر Secret Key
```bash
# تولید secret key قوی
python -c "import secrets; print(secrets.token_urlsafe(32))"

# تنظیم در Railway
railway variables set SECRET_KEY=your-generated-key
```

### 2. محدودیت دسترسی
```python
# در server.py می‌توانید IP whitelist اضافه کنید
ALLOWED_IPS = ['127.0.0.1', '::1']
```

### 3. Rate Limiting
```python
# محدودیت درخواست
RATE_LIMIT = 100  # درخواست در دقیقه
```

---

## 📊 مانیتورینگ

### 1. Railway Dashboard
- **Metrics**: CPU، Memory، Network
- **Logs**: لاگ‌های real-time
- **Deployments**: تاریخچه استقرارها

### 2. Health Check
```bash
# بررسی وضعیت سرور
curl https://your-app-name.railway.app/status

# پاسخ مورد انتظار:
{
  "status": "healthy",
  "message": "سرویس در حال اجرا است",
  "environment": "production",
  "debug": false
}
```

---

## 🐛 عیب‌یابی

### مشکلات رایج

#### 1. خطای "Build Failed"
```bash
# بررسی لاگ‌های build
railway logs --build

# معمولاً مشکل از requirements.txt است
pip install -r requirements.txt
```

#### 2. خطای "Port not found"
```bash
# بررسی متغیر PORT
railway variables

# تنظیم مجدد
railway variables set PORT=8443
```

#### 3. خطای "Module not found"
```bash
# بررسی ساختار پروژه
# مطمئن شوید anti_filter_bridge/__init__.py موجود است
```

### لاگ‌های مفید
```bash
# لاگ‌های کامل
railway logs

# لاگ‌های real-time
railway logs --follow

# لاگ‌های build
railway logs --build
```

---

## 🔄 به‌روزرسانی

### استقرار مجدد
```bash
# از طریق GitHub (خودکار)
git add .
git commit -m "Update server"
git push origin main

# یا از طریق Railway CLI
railway up
```

### Rollback
```bash
# بازگشت به نسخه قبلی
railway rollback
```

---

## 💰 هزینه‌ها

### پلان رایگان
- ✅ 500 ساعت در ماه
- ✅ 1GB RAM
- ✅ 1GB Storage
- ✅ دامنه رایگان
- ✅ SSL خودکار

### پلان Pro ($5/ماه)
- ✅ ساعت نامحدود
- ✅ 8GB RAM
- ✅ 100GB Storage
- ✅ دامنه‌های نامحدود

---

## 🎯 نتیجه

پس از تکمیل این مراحل:
1. ✅ سرور شما روی Railway اجرا می‌شود
2. ✅ دامنه رایگان دریافت می‌کنید
3. ✅ SSL خودکار فعال است
4. ✅ می‌توانید از کلاینت متصل شوید

**URL سرور:** `https://your-app-name.railway.app`
**WebSocket:** `wss://your-app-name.railway.app`

---

## 📞 پشتیبانی

- **Railway Docs**: [docs.railway.app](https://docs.railway.app)
- **GitHub Issues**: برای مشکلات پروژه
- **Discord**: Railway community

**موفق باشید! 🚀**
