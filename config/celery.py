import os
from celery import Celery

# Set default django settings for celery program
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Create celery app
app = Celery('config')

# Configure settings using django settings.py
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load tasks from all registered Django app configs
app.autodiscover_tasks()
