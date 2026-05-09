#!/bin/bash
# Simple deployment script

echo "🚀 Deploying portfolio..."

# Pull latest changes
git pull origin main

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Restart gunicorn (if using systemd)
sudo systemctl restart gunicorn-portfolio

# Or restart with supervisor
# sudo supervisorctl restart portfolio

echo "✅ Deployment complete!"
