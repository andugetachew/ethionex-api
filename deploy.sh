#!/bin/bash

# Deploy script for EthioNex API

echo "🚀 Starting EthioNex API Deployment..."

# Pull latest code
git pull origin main

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Restart services
sudo systemctl restart gunicorn
sudo systemctl restart nginx

# Clear cache
python manage.py clear_cache

echo "✅ Deployment complete!"