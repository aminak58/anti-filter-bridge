# راهنمای سریع نصب و اجرا - Anti-Filter Bridge

## پیش‌نیازها

- Python 3.8 یا بالاتر
- pip (مدیریت بسته‌های پایتون)
- OpenSSL (برای تولید گواهی‌های SSL)

## نصب سریع (5 دقیقه)

### 1. کلون کردن پروژه

```bash
git clone <repository-url>
cd anti_filter_bridge
```

### 2. نصب وابستگی‌ها

```bash
# نصب در حالت توسعه
pip install -e .

# یا نصب مستقیم
pip install -r requirements.txt
```

### 3. تولید گواهی‌های SSL (برای تست)

```bash
# تولید گواهی خودامضا برای تست
python generate_certs.py
```

### 4. تنظیم متغیرهای محیطی

```bash
# کپی کردن فایل نمونه
cp env.example .env

# ویرایش تنظیمات (اختیاری)
# nano .env
```

## اجرای سرور

### روش 1: اجرای مستقیم

```bash
# اجرای سرور با گواهی SSL
python -m anti_filter_bridge.server --certfile certs/cert.pem --keyfile certs/key.pem

# یا بدون SSL (فقط برای تست)
python -m anti_filter_bridge.server
```

### روش 2: اجرای با تنظیمات سفارشی

```bash
python -m anti_filter_bridge.server \
  --host 0.0.0.0 \
  --port 8443 \
  --certfile certs/cert.pem \
  --keyfile certs/key.pem \
  --log-level INFO
```

## اجرای کلاینت

### روش 1: اجرای مستقیم

```bash
# اتصال به سرور محلی
python client.py --server ws://localhost:8081 --local-port 1080

# اتصال به سرور با SSL
python client.py --server wss://localhost:8443 --local-port 1080
```

### روش 2: استفاده از CLI

```bash
# شروع کلاینت
afb start --server wss://your-server-address:8443 --local-port 1080

# با تنظیمات کامل
afb start \
  --server wss://your-server-address:8443 \
  --local-port 1080 \
  --log-level DEBUG
```

## تست اتصال

### 1. بررسی وضعیت سرور

```bash
# بررسی لاگ‌های سرور
tail -f logs/server.log

# یا بررسی وضعیت
curl http://localhost:8000/status
```

### 2. تست کلاینت

```bash
# بررسی لاگ‌های کلاینت
tail -f logs/client.log

# تست اتصال SOCKS5
curl --socks5 127.0.0.1:1080 http://httpbin.org/ip
```

### 3. تنظیم مرورگر

1. باز کردن تنظیمات پروکسی مرورگر
2. تنظیم پروکسی SOCKS5:
   - آدرس: `127.0.0.1`
   - پورت: `1080`
3. تست دسترسی به سایت‌های مسدود شده

## عیب‌یابی

### مشکلات رایج

#### 1. خطای "Port already in use"

```bash
# پیدا کردن فرآیند استفاده‌کننده از پورت
netstat -tulpn | grep :8443

# یا در ویندوز
netstat -ano | findstr :8443

# کشتن فرآیند
kill -9 <PID>
```

#### 2. خطای SSL Certificate

```bash
# استفاده از گزینه --insecure (فقط برای تست)
python client.py --server wss://localhost:8443 --insecure

# یا تولید مجدد گواهی
python generate_certs.py
```

#### 3. خطای اتصال

```bash
# بررسی فایروال
sudo ufw status

# بررسی پورت‌های باز
ss -tulpn | grep :8443
```

### بررسی لاگ‌ها

```bash
# لاگ‌های سرور
tail -f logs/server.log

# لاگ‌های کلاینت
tail -f logs/client.log

# لاگ‌های سیستم
journalctl -u anti-filter-bridge -f
```

## تنظیمات پیشرفته

### 1. اجرا به عنوان سرویس سیستم

```bash
# کپی فایل سرویس
sudo cp deploy/config/systemd/anti-filter-bridge.service /etc/systemd/system/

# فعال‌سازی سرویس
sudo systemctl enable anti-filter-bridge
sudo systemctl start anti-filter-bridge

# بررسی وضعیت
sudo systemctl status anti-filter-bridge
```

### 2. تنظیم Nginx (اختیاری)

```bash
# کپی فایل تنظیمات Nginx
sudo cp deploy/config/nginx/anti-filter-bridge.conf /etc/nginx/sites-available/

# فعال‌سازی سایت
sudo ln -s /etc/nginx/sites-available/anti-filter-bridge.conf /etc/nginx/sites-enabled/

# بارگذاری مجدد Nginx
sudo nginx -t
sudo systemctl reload nginx
```

## امنیت

### 1. تغییر تنظیمات پیش‌فرض

```bash
# ویرایش فایل .env
nano .env

# تغییر secret_key
SECRET_KEY=your-very-secure-secret-key-here

# تغییر پورت‌ها
PORT=8443
CLIENT_LOCAL_PORT=1080
```

### 2. استفاده از گواهی معتبر

```bash
# جایگزینی گواهی خودامضا با گواهی معتبر
cp your-cert.pem certs/cert.pem
cp your-key.pem certs/key.pem
```

## پشتیبانی

- **مستندات کامل**: `docs/`
- **مثال‌ها**: `examples/`
- **مشکلات**: GitHub Issues
- **لاگ‌ها**: `logs/`

---

**نکته**: این راهنما برای تست و توسعه است. برای استفاده در محیط تولید، لطفاً تنظیمات امنیتی را بررسی کنید.
