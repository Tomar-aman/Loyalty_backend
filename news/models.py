from django.db import models
from django.utils.translation import gettext_lazy as _
class NewsArticle(models.Model):
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
    published_at = models.DateTimeField(
        _("Published At"),
        auto_now_add=True,
    )
    def __str__(self):
        return self.title if self.title else "Untitled Article"
