
import os
from celery import Celery


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'authentication.settings')

app = Celery('authentication')
app.config_from_object('django.conf:settings', namespace='CELERY')
# app.conf.enable_utc = False
# app.conf.update(timezone='Asia/Kolkata')
# app.conf.broker_connection_retry_on_startup = True

# Remove direct imports and use autodiscovery
app.autodiscover_tasks()
