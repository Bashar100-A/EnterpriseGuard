FROM python:3.12-slim

WORKDIR /app

# نسخ الملفات الأساسية
COPY tools/ ./tools/
COPY continuity/ ./continuity/
COPY docs/ ./docs/
COPY README_AAAC.md ./README.md

# تثبيت المتطلبات الأساسية فقط
RUN pip install --no-cache-dir requests langfuse

# المنفذ
EXPOSE 8443

# تشغيل الخادم السيادي
CMD ["python3", "tools/sovereign_http_server.py", "--host", "0.0.0.0", "--port", "8443"]
