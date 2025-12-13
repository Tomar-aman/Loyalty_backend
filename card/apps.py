from django.apps import AppConfig


class CardConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'card'

    def ready(self):
        from .scheduler import start_scheduler
        start_scheduler()
