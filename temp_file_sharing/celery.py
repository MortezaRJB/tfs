from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'temp_file_sharing.settings')

app = Celery('temp_file_sharing')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Periodic tasks
from celery.schedules import crontab

app.conf.beat_schedule = {
    'cleanup-expired-files': {
        'task': 'file_sharing.tasks.cleanup_expired_files',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
    },
    'cleanup-old-files': {
        'task': 'file_sharing.tasks.cleanup_old_inactive_files',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
    },
}
app.conf.timezone = 'UTC'


