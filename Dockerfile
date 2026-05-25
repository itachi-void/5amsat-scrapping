FROM python:3.10-slim

WORKDIR /app

# تثبيت dependencies النظام
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# تثبيت مكتبات Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# نسخ باقي الملفات
COPY . .

# إنشاء سكربت بدء التشغيل الذي يقوم بتثبيت المتصفحات ثم تشغيل البوت
RUN echo '#!/bin/bash\necho "Installing Playwright browsers..."\nplaywright install chromium\necho "Browsers installed. Starting bot..."\npython 5.py' > start.sh && chmod +x start.sh

CMD ["./start.sh"]
