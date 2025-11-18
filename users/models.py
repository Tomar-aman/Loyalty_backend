from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from users.managers import UserManager

class User(AbstractUser):
    username = None
    first_name = models.CharField(
        _('first name'),    
        max_length=150,
        blank=True,
        help_text=_('Optional first name of the user.')
    )
    last_name = models.CharField(
        _('last name'),
        max_length=150,
        blank=True,
        help_text=_('Optional last name of the user.')
    )
    country_code = models.CharField(
        _('country code'),
        max_length=5,
        null=True,
        blank=True,
    )
    phone_number = models.CharField(
        _('phone number'),
        max_length=18,
        unique=True,
        null=True,
        blank=True,
        error_messages={
            'unique': _("A user with that phone number already exists."),
        },
    )
    is_admin = models.BooleanField(
        _('admin status'),
        default=False,
        help_text=_('Designates whether the user is an admin.'),
    )
    is_superadmin = models.BooleanField(
        _('superadmin status'),
        default=False,
        help_text=_('Designates whether the user is a super admin.'),
    )
    email = models.EmailField(
        _("email"),
        unique=True,
        error_messages={
            'unique': _("A user with that email already exists."),
            'invalid': _("Invalid email address."),
            },
        null=True,
        blank=True 
        )
    profile_picture = models.ImageField(
        _('profile picture'),
        upload_to='profile_pictures/',
        null=True,
        blank=True
    )
    google_id = models.CharField(
        _('google id'),
        max_length=255,
        unique=True,
        null=True,
        blank=True,
        error_messages={
            'unique': _("A user with that Google ID already exists."),
        },
    )
    facebook_id = models.CharField(
        _('facebook id'),
        max_length=255,
        unique=True,
        null=True,
        blank=True,
        error_messages={
            'unique': _("A user with that Facebook ID already exists."),
        },
    )

    apple_id = models.CharField(
        _('apple id'),
        max_length=255,
        unique=True,
        null=True,
        blank=True,
        error_messages={
            'unique': _("A user with that Apple ID already exists."),
        },
    )   

    stripe_customer_id = models.CharField(
        _('stripe customer id'),
        max_length=255,
        null=True,
        blank=True,
        help_text=_('Stripe customer id')
    )


    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = UserManager()

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def __str__(self):
        return f"{self.first_name} - {self.email}"

class OTP(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=_('user'),
        help_text=_('The user associated with this OTP')
    )
    otp_code = models.CharField(
        _('OTP code'),
        max_length=6,
        help_text=_('One-time password code for verification')
    )
    created_at = models.DateTimeField(
        _('created at'),
        auto_now_add=True,
        db_index=True
    )
    expires_at = models.DateTimeField(
        _('expires at'),
        null=True,
        blank=True,
        help_text=_('Expiration time for the OTP code')
    )

    class Meta:
        verbose_name = _('OTP')
        verbose_name_plural = _('OTPs')

    def __str__(self):
        return f"OTP for {self.user.first_name} - {self.otp_code}"
    
    def is_expired(self):
        """
        Check if the OTP has expired.
        """
        from django.utils import timezone
        return timezone.now() > self.expires_at if self.expires_at else True