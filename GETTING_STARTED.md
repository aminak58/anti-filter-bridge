# راهنمای شروع سریع - Anti-Filter Bridge

## 🎉 تبریک! پروژه آماده اجرا است

تمام خطاها برطرف شده و پروژه آماده استفاده است.

## ⚡ اجرای فوری (2 دقیقه)

### 1. نصب وابستگی‌ها
```bash
pip install -e .
```

### 2. تولید گواهی SSL
```bash
python generate_certs.py
```

### 3. اجرای سرور
```bash
python -m anti_filter_bridge.server --certfile certs/cert.pem --keyfile certs/key.pem
```

### 4. اجرای کلاینت (در ترمینال جدید)
```bash
python client.py --server wss://localhost:8443 --local-port 1080
```

### 5. تنظیم مرورگر
- آدرس پروکسی: `127.0.0.1`
- پورت: `1080`
- نوع: SOCKS5

## 🔧 اسکریپت‌های خودکار

### Windows
```cmd
setup.bat
```

### Linux/macOS
```bash
chmod +x setup.sh
./setup.sh
```

## 🧪 تست نصب
```bash
python test_installation.py
```

## 📚 مستندات کامل
- `QUICKSTART.md` - راهنمای کامل
- `README.md` - مستندات اصلی
- `specs/` - مستندات فنی

## 🐛 عیب‌یابی

### اگر سرور شروع نشد:
```bash
# بررسی پورت
netstat -an | findstr :8443

# اجرا بدون SSL (فقط برای تست)
python -m anti_filter_bridge.server
```

### اگر کلاینت متصل نشد:
```bash
# استفاده از --insecure
python client.py --server wss://localhost:8443 --insecure

# یا بدون SSL
python client.py --server ws://localhost:8081
```

## 📊 وضعیت پروژه

✅ **خطاهای syntax برطرف شدند**
✅ **Import ها اصلاح شدند**  
✅ **تنظیمات پیش‌فرض اضافه شدند**
✅ **فایل‌های تکراری حذف شدند**
✅ **گواهی‌های SSL تولید شدند**
✅ **راهنمای کامل ایجاد شد**
✅ **اسکریپت‌های خودکار آماده شدند**

## 🚀 آماده برای استفاده!

پروژه حالا کاملاً آماده است و می‌توانید از آن استفاده کنید.
