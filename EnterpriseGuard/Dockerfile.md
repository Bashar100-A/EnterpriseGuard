# استخدام نسخة Python 3.12 خفيفة ومستقرة
FROM python:3.12-slim

# ضبط متغيرات البيئة لمنع كتابة ملفات pyc وتحديث السجلات فوراً
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# تحديد مجلد العمل داخل الحاوية
WORKDIR /app

# تثبيت الحزم والنظام الأساسي
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# تثبيت المكتبات البرمجية المطلوبة للمشروع
RUN pip install --no-cache-dir \
    fastapi \
    "uvicorn[standard]" \
    cryptography \
    pydantic \
    websockets

# نسخ كافة ملفات المشروع إلى الحاوية
COPY . /app/

# إنشاء مجلد الخزنة المحصنة SIBB
RUN mkdir -p /app/sibb_vault

# كشف المنفذ 8000
EXPOSE 8000

# أمر تشغيل الخادم عند بدء الحاوية
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
