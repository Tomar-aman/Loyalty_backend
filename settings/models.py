from django.db import models
from django.utils.translation import gettext_lazy as _
from config.models import BaseModel

class SMTPSettings(models.Model):
    host = models.CharField(
        _('SMTP Host'),
        max_length=255,
        help_text=_('SMTP server hostname')
    )
    port = models.IntegerField(
        _('SMTP Port'),
        help_text=_('SMTP server port number')
    )
    username = models.CharField(
        _('SMTP Username'),
        max_length=255,
        help_text=_('SMTP authentication username')
    )
    password = models.CharField(
        _('SMTP Password'),
        max_length=255,
        help_text=_('SMTP authentication password')
    )
    from_email = models.EmailField(
        _('From Email'),
        help_text=_('Default sender email address')
    )
    use_tls = models.BooleanField(
        _('Use TLS'),
        default=True,
        help_text=_('Enable TLS encryption for SMTP connection')
    )
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        verbose_name = _('SMTP Setting')
        verbose_name_plural = _('SMTP Settings')
        ordering = ['-updated_at']

    def __str__(self):
        return f"SMTP Settings - {self.host} ({self.username})"

class GoogleMapsSettings(BaseModel):
    api_key = models.CharField(
        _('Google Maps API Key'),
        max_length=255,
        help_text=_('API key for Google Maps services')
    )
    class Meta:
        verbose_name = _('Google Maps Setting')
        verbose_name_plural = _('Google Maps Settings')
        ordering = ['-updated_at']

    def __str__(self):
        return f"Google Maps API Key - {self.api_key[:10]}..."

class StipeKeySettings(BaseModel):
    public_key = models.CharField(
        _('Stripe Public Key'),
        max_length=255,
        help_text=_('Public key for Stripe payment gateway')
    )
    secret_key = models.CharField(
        _('Stripe Secret Key'),
        max_length=255,
        help_text=_('Secret key for Stripe payment gateway')
    )
    webhook_secret = models.CharField(
        _('Webhook Secret'),
        max_length=255,
        help_text=_('Starts with whsec_... Get this from Stripe Dashboard → Developers → Webhooks'),
        blank=True,
        null=True
    )
    currency = models.CharField(
        _('Default Currency'),
        max_length=3,
        default='USD',
        help_text=_('Default currency for Stripe transactions')
    )
    version = models.CharField(
        _('Stripe API Version'),
        max_length=50,
        help_text=_('API version for Stripe integration')
    )

    class Meta:
        verbose_name = _('Stripe Key Setting')
        verbose_name_plural = _('Stripe Key Settings')
        ordering = ['-updated_at']

    def __str__(self):
        return f"Stripe Keys - {self.public_key[:10]}..."


class FirebaseSettings(models.Model):
    file_name = models.CharField(
        max_length=255,
        verbose_name=_('file name'),
        help_text=_('Notification settings file name'),
        null=True,
        blank=True,
    )
    config_file = models.FileField(
        upload_to='firebase/',
        verbose_name=_('config file'),
        help_text=_('Notification settings configuration file'),
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('created at'),
        help_text=_('Date and time when the notification settings were created'),
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('updated at'),
        help_text=_('Date and time when the notification settings were last updated'),
    )

    def __str__(self):
        return self.file_name

    def save(self, *args, **kwargs):
        if not self.pk:
            self.file_name = self.config_file.name
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = _('Firebase Setting')
        verbose_name_plural = _('Firebase Settings')
        ordering = ['-updated_at']