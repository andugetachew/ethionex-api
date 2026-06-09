import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ethionex_api.settings")

app = Celery("ethionex_api")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")


app.conf.beat_schedule = {
    "database-backup-daily": {
        "task": "notifications.tasks.automated_database_backup",
        "schedule": crontab(hour=2, minute=0),  # Run at 2 AM daily
    },
}
