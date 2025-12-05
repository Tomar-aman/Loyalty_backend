from django.db import models
from config.models import BaseModel
from django.utils.translation import gettext_lazy as _

class Support(BaseModel):
    country_code = models.CharField(
        _("Country Code"),
        max_length=5
    )
    phone_number = models.CharField(
        _("Phone Number"),
        max_length=15
      )
    email = models.EmailField(
        _("Email Address"),
        max_length=254
    )
    class Meta:
        verbose_name = _("Support Contact")
        verbose_name_plural = _("Support Contacts")


class FAQ(BaseModel):
    question = models.CharField(
        _("Question"),
        max_length=500
    )
    answer = models.TextField(
        _("Answer")
    )
    is_active = models.BooleanField(
        _("Is Active"),
        default=True,
        help_text=_("Designates whether this FAQ should be treated as active. Unselect this instead of deleting FAQs.")
    )

    class Meta:
        verbose_name = _("Frequently Asked Question")
        verbose_name_plural = _("Frequently Asked Questions")


class ContactUsMessage(BaseModel):
    name = models.CharField(
        _("Name"),
        max_length=255
    )
    email = models.EmailField(
        _("Email Address"),
        max_length=254
    )
    subject = models.CharField(
        _("Subject"),
        max_length=255
    )
    message = models.TextField(
        _("Message")
    )
    is_resolved = models.BooleanField(
        _("Is Resolved"),
        default=False,
        help_text=_("Designates whether this message has been resolved.")
    )

    class Meta:
        verbose_name = _("Contact Us Message")
        verbose_name_plural = _("Contact Us Messages")
    