from django.db import models
from django.utils.translation import gettext_lazy as _
from config.models import BaseModel
from users.models import User

class Notification(BaseModel):
    user = models.ForeignKey(
        User,
        related_name="notifications",
        on_delete=models.CASCADE
    )
    title = models.CharField(
        max_length=255,
        help_text=_("Title of the notification")
    )
    message = models.TextField(
        help_text=_("Content of the notification")
    )
    is_read = models.BooleanField(
        default=False,
        help_text=_("Indicates whether the notification has been read")
    )

    def __str__(self):
        return f"Notification for {self.user.username}: {self.title}"

    class Meta:
        verbose_name = _("Notification")
        verbose_name_plural = _("Notifications")
        ordering = ['-created_at']