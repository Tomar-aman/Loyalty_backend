from django.db import models
from django.utils.translation import gettext_lazy as _
from config.models import BaseModel
from users.models import User

class Card(models.Model):
    DURATION_CHOICES = [
        ('1_day', '1 Day'),
        ('1_week', '1 Week'),
        ('1_month', '1 Month'),
        ('1_year', '1 Month'),
    ]
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text=_("Name of the card")
    )
    duration = models.CharField(
        max_length=20, 
        choices=DURATION_CHOICES,
        help_text=_("Duration of the card validity")
    )
    price = models.DecimalField(
        max_digits=6, 
        decimal_places=2,
        help_text=_("Price of the card")
    )

    short_description = models.CharField(
        max_length=255,
        help_text=_("Short description of the card"),
        blank=True,
        null=True
    )

    is_active = models.BooleanField(
        default=True,
        help_text=_("Indicates whether the card is active")
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text=_("Timestamp when the card was created")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text=_("Timestamp when the card was last updated")
    )
    def __str__(self):
        return f"{self.name} - {self.get_duration_display()}"
    class Meta:
        verbose_name = _("Card")
        verbose_name_plural = _("Cards")
        ordering = ['-created_at']

class CardBenefit(models.Model):
    card = models.ForeignKey(
        Card,
        related_name="benefits",
        on_delete=models.CASCADE
    )
    title = models.CharField(
        max_length=100,
        help_text=_("Title of the benefit")
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text=_("Description of the benefit")
    )
    icon = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text=_("Icon name or class for the benefit")
    )

    def __str__(self):
        return f"{self.title} ({self.card.name})"

    class Meta:
        verbose_name = _("Card Benefit")
        verbose_name_plural = _("Card Benefits")


class UserCard(BaseModel):
    user = models.ForeignKey(
        User,
        on_delete=models.DO_NOTHING,
        related_name="user_cards",
        verbose_name=_("user")
    )
    card = models.ForeignKey(
        Card,
        on_delete=models.DO_NOTHING,
        related_name="users_card",
        verbose_name=_("card")
    )
    start_at = models.DateTimeField(
        verbose_name=_("start at"),
        auto_now_add=True
    )
    end_at = models.DateTimeField(
        verbose_name=_("end at")
    )
    is_active = models.BooleanField(
        _('is active'),
        default=True,
        help_text=_('Designates whether this user card is active.')
    )

    def __str__(self):
        return f'UserCard {self.id} - User: {self.user_id} - Card: {self.card.name}'

    class Meta:
        verbose_name = _("user card")
        verbose_name_plural = _("user cards")

class UserCardHistory(BaseModel):
    ACTION_TYPES = (
        ('purchase', 'Purchase'),
        ('renew', 'Renew'),
        ('auto_expire', 'Auto Expire'),
        ('cancel', 'Cancel'),
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name="card_history",
        verbose_name=_("user")
    )
    card = models.ForeignKey(
        Card, 
        on_delete=models.CASCADE, 
        related_name="card_history",
        verbose_name=_("card")
    )
    action = models.CharField(
        verbose_name=_("action"),
        max_length=20, 
        choices=ACTION_TYPES
        )
    start_at = models.DateTimeField(
        verbose_name=_("start at")
    )
    end_at = models.DateTimeField(
        verbose_name=_("end at")
    )

    def __str__(self):
        return f"{self.user} - {self.card} - {self.action}"
