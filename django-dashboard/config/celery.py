import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('ai_devops_platform', broker='redis://localhost:6379/0')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()
