"""
نقطه ورود اصلی برنامه Anti-Filter Bridge

این فایل سرور اصلی برنامه را راه‌اندازی می‌کند.
"""
import uvicorn
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from src.core.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    مدیریت چرخه حیات برنامه
    """
    # کدهای قبل از شروع برنامه
    print(f"شروع برنامه {settings.app_name} در حالت {settings.app_env}")
    
    yield
    
    # کدهای قبل از خاتمه برنامه
    print("در حال خاتمه برنامه...")

# ایجاد برنامه FastAPI با مدیریت چرخه حیات
app = FastAPI(
    title=settings.app_name,
    description="یک پل امن برای عبور از فیلترینگ اینترنت",
    version="0.1.0",
    debug=settings.debug,
    lifespan=lifespan,
)

# تنظیم CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins if hasattr(settings, 'cors_origins') else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# مسیر اصلی
@app.get("/")
async def root():
    """
    مسیر اصلی برنامه
    """
    return {
        "message": f"به سرویس {settings.app_name} خوش آمدید!",
        "version": "0.1.0",
        "environment": settings.app_env,
        "docs": "/docs",
    }

# مسیر وضعیت سرویس
@app.get("/status")
async def status():
    """
    بررسی وضعیت سرویس
    """
    return {
        "status": "active", 
        "message": "سرویس در حال اجرا است",
        "environment": settings.app_env,
        "debug": settings.debug,
    }

# مسیر اطلاعات تنظیمات (فقط در حالت توسعه)
if settings.debug:
    @app.get("/settings")
    async def show_settings():
        """
        نمایش تنظیمات برنامه (فقط در حالت توسعه)
        """
        return {
            "app_name": settings.app_name,
            "app_env": settings.app_env,
            "debug": settings.debug,
            "host": settings.host,
            "port": settings.port,
        }

if __name__ == "__main__":
    # اجرای سرور با uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        workers=settings.workers,
    )
