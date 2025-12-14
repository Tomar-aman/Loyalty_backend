from django.apps import AppConfig
import os

class NotificationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'notification'

    def ready(self):
        if os.environ.get("RUN_MAIN") == "true":
            from .firebase import init_firebase
