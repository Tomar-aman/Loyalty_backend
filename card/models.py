from django.db import models
from django.utils.translation import gettext_lazy as _

class Card(models.Model):
    DURATION_CHOICES = [
        ('1_day', '1 Day'),
        ('1_week', '1 Week'),
        ('1_month', '1 Month'),
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
