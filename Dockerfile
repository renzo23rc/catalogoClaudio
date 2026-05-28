FROM python:3.12-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Project
COPY . .

# Static files
RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "catalogo.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4"]
