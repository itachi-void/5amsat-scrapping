FROM python:3.10-slim

WORKDIR /app

# تثبيت dependencies النظام لتشغيل المتصفحات
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# تثبيت مكتبات Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    playwright install chromium && \
    playwright install-deps

# تحديد مسار ثابت للمتصفحات (يمنع حذفها من Railway)
ENV PLAYWRIGHT_BROWSERS_PATH=/app/ms-playwright

COPY . .

CMD ["python", "5.py"]
