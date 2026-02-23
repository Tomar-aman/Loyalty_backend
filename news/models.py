from django.db import models
from django.utils.translation import gettext_lazy as _
from config.models import BaseModel
from business.models import BusinessCategory
from users.models import City

class NewsArticle(BaseModel):
    title = models.TextField(
        _("Title"),
        null=True,
        blank=True,
    )
    content = models.TextField(
        _("Content"),
        null=True,
        blank=True,
    )
    icon = models.ImageField(
        _("Icon"),
        upload_to='news_icons/',
        null=True,
        blank=True,
    )
    category = models.ForeignKey(
        BusinessCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Business Category"),
        help_text=_("The business category this news article relates to"),
    )
    city = models.ForeignKey(
        City,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("City"),
        help_text=_("The city this news article is relevant to"),
    )
    published_at = models.DateTimeField(
        _("Published At"),
        auto_now_add=True,
    )
    def __str__(self):
        return self.title if self.title else "Untitled Article"
