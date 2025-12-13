from django.apps import AppConfig
import os
import threading

class CardConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'card'

    def ready(self):
        # Only run scheduler in main process
        if os.environ.get("RUN_MAIN") == "true":
            from .scheduler import start_scheduler

            # Start scheduler in a new thread
            threading.Thread(target=start_scheduler).start()
