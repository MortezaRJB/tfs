FROM python:3.11-slim

# تنظیم متغیرهای محیطی
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# نصب dependencies سیستمی
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    gettext \
    && rm -rf /var/lib/apt/lists/*

# ایجاد کاربر غیر root
RUN useradd --create-home --shell /bin/bash app

# تنظیم مسیر کاری
WORKDIR /app

# کپی requirements و نصب Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# کپی کد پروژه
COPY . .

# تنظیم مالکیت فایل‌ها
RUN chown -R app:app /app

# تغییر به کاربر app
USER app

# ایجاد دایرکتوری‌های مورد نیاز
RUN mkdir -p media/temp_files logs staticfiles

# Expose کردن پورت
EXPOSE 8000

# دستور پیش‌فرض
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "temp_file_sharing.wsgi:application"]
