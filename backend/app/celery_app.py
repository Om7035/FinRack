"""Celery application configuration"""
from celery import Celery
from celery.schedules import crontab
from app.config import settings

# Create Celery app
celery_app = Celery(
    'finrack',
    broker=settings.RABBITMQ_URL,
    backend=settings.REDIS_URL,
    include=['app.services.transaction_sync']
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Periodic tasks
celery_app.conf.beat_schedule = {
    'sync-all-accounts': {
        'task': 'app.services.transaction_sync.sync_all_accounts',
        'schedule': crontab(minute='*/30'),  # Every 30 minutes
    },
}
