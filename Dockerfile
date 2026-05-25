FROM python:3.10-slim

WORKDIR /app

# System dependencies المطلوبة لـ Playwright
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    curl \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    xdg-utils \
    libu2f-udev \
    libvulkan1 \
    && rm -rf /var/lib/apt/lists/*

# تثبيت Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# تثبيت متصفحات Playwright أثناء build
RUN playwright install --with-deps chromium

# نسخ ملفات المشروع
COPY . .

# تشغيل البوت
CMD ["python", "5.py"]
