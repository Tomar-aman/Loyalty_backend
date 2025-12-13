from django_apscheduler.jobstores import DjangoJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from django.utils import timezone
from card.models import UserCard, UserCardHistory

def expire_cards_job():
    now = timezone.now()

    expired_cards = UserCard.objects.filter(
        is_active=True,
        end_at__lt=now
    )

    for uc in expired_cards:
        uc.is_active = False
        uc.save()

        UserCardHistory.objects.create(
            user=uc.user,
            card=uc.card,
            action="auto_expire",
            start_at=uc.start_at,
            end_at=uc.end_at
        )

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_jobstore(DjangoJobStore(), "default")

    # run every 1 minute
    scheduler.add_job(
        expire_cards_job,
        "interval",
        minutes=180,
        id="expire_cards_job",
        replace_existing=True
    )

    scheduler.start()
