# Anti-Filter Bridge

یک پل امن برای عبور از فیلترینگ اینترنت با استفاده از WebSocket و رمزنگاری پیشرفته

## ✨ ویژگی‌های کلیدی

- 🛡️ تونل امن با استفاده از WebSocket (WSS)
- 🔒 رمزنگاری پیشرفته ترافیک
- ⚡ عملکرد سریع با بهینه‌سازی حافظه
- 🔄 قابلیت اتصال مجدد خودکار
- 🔌 پشتیبانی از پروکسی SOCKS5
- 📊 لاگ‌گیری پیشرفته

## 🚀 نصب سریع

### پیش‌نیازها
- Python 3.8 یا بالاتر
- pip (مدیریت بسته‌های پایتون)

### نصب
```bash
# کلون کردن پروژه
git clone https://github.com/yourusername/anti-filter-bridge.git
cd anti-filter-bridge

# نصب وابستگی‌ها
pip install -r requirements.txt

# یا نصب در حالت توسعه
pip install -e .
```

## ⚡ اجرای فوری

### 1. تولید گواهی SSL
```bash
python generate_certs.py
```

### 2. اجرای سرور
```bash
python -m anti_filter_bridge.server --certfile certs/cert.pem --keyfile certs/key.pem
```

### 3. اجرای کلاینت (در ترمینال جدید)
```bash
python client.py --server wss://localhost:8443 --local-port 1080
```

### 4. تنظیم مرورگر
- **آدرس پروکسی**: `127.0.0.1`
- **پورت**: `1080`
- **نوع**: SOCKS5

## 🌐 استقرار روی سرویس‌های رایگان

### Railway (توصیه شده)
1. ثبت‌نام در [railway.app](https://railway.app)
2. اتصال GitHub repository
3. Deploy خودکار

برای جزئیات بیشتر: [RAILWAY_DEPLOY.md](RAILWAY_DEPLOY.md)

### سایر گزینه‌ها
- **Heroku**: [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
- **Render**: [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
- **Docker**: [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)

## 📚 مستندات

- [QUICKSTART.md](QUICKSTART.md) - راهنمای کامل نصب و اجرا
- [GETTING_STARTED.md](GETTING_STARTED.md) - راهنمای شروع سریع
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - راهنمای استقرار
- [RAILWAY_DEPLOY.md](RAILWAY_DEPLOY.md) - راهنمای Railway

## 🧪 تست نصب

```bash
python test_installation.py
```

## 🔧 تنظیمات پیشرفته

### متغیرهای محیطی
```bash
# کپی کردن فایل نمونه
cp env.example .env

# ویرایش تنظیمات
nano .env
```

### گزینه‌های خط فرمان

#### سرور
```bash
python -m anti_filter_bridge.server --help
```

#### کلاینت
```bash
python client.py --help
```

## 🐛 عیب‌یابی

### مشکلات رایج

#### 1. خطای "Port already in use"
```bash
# پیدا کردن فرآیند
netstat -ano | findstr :8443

# کشتن فرآیند
taskkill /PID <PID> /F
```

#### 2. خطای SSL Certificate
```bash
# استفاده از --insecure (فقط برای تست)
python client.py --server wss://localhost:8443 --insecure
```

#### 3. خطای اتصال
```bash
# بررسی فایروال
# بررسی پورت‌های باز
```

## 📊 وضعیت پروژه

- ✅ **نسخه**: 0.1.0
- ✅ **وضعیت**: آماده استفاده
- ✅ **تست‌ها**: 6/6 موفق
- ✅ **مستندات**: کامل

## 🤝 مشارکت

مشارکت‌های شما استقبال می‌شود! لطفاً:

1. Fork کنید
2. Branch جدید ایجاد کنید (`git checkout -b feature/amazing-feature`)
3. تغییرات را commit کنید (`git commit -m 'Add amazing feature'`)
4. Push کنید (`git push origin feature/amazing-feature`)
5. Pull Request ایجاد کنید

## 📄 مجوز

این پروژه تحت مجوز MIT منتشر شده است. برای اطلاعات بیشتر فایل `LICENSE` را ببینید.

## 📞 پشتیبانی

- **GitHub Issues**: برای گزارش باگ و درخواست ویژگی
- **Discussions**: برای سوالات و بحث
- **Email**: your.email@example.com

---

**نکته**: این پروژه فقط برای اهداف آموزشی و تحقیقاتی است. لطفاً قوانین محلی خود را رعایت کنید.