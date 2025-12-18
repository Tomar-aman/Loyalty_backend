from django.db import models
from django.utils.translation import gettext_lazy as _
from users.models import User

class BusinessCategory(models.Model):
    name = models.CharField(
        _("Category Name"),
        max_length=255,
        unique=True,
    )
    icon = models.ImageField(
        _("Icon"),
        upload_to='category_icons/',
        null=True,
        blank=True,
    )
    is_active = models.BooleanField(
        _("Is Active"),
        default=True,
    )
    created_at = models.DateTimeField(
        _("Created At"),
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        _("Updated At"),
        auto_now=True,
    )

    def __str__(self):
        return self.name
    
class Business(models.Model):
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='businesses',
        verbose_name=_("Owner"),
    )
    name = models.CharField(
        _("Business Name"),
        max_length=255,
    )
    logo = models.ImageField(
        _("Logo"),
        upload_to='business_logos/',
        null=True,
        blank=True,
    )
    category = models.ForeignKey(
        BusinessCategory,
        on_delete=models.CASCADE,
        related_name='businesses',
        verbose_name=_("Category"),
    )
    description = models.TextField(
        _("Description"),
        null=True,
        blank=True,
    )
    address = models.TextField(
        _("Address"),
        null=True,
        blank=True,
    )
    latitude = models.DecimalField(
        _("Latitude"),
        max_digits=15,
        decimal_places=6,
        null=True,
        blank=True,
    )
    longitude = models.DecimalField(
        _("Longitude"),
        max_digits=15,
        decimal_places=6,
        null=True,
        blank=True,
    )
    phone_number = models.CharField(
        _("Phone Number"),
        max_length=20,
        null=True,
        blank=True,
    )
    email = models.EmailField(
        _("Email"),
        null=True,
        blank=True,
    )
    website = models.URLField(
        _("Website"),
        null=True,
        blank=True,
    )
    is_featured = models.BooleanField(
        _("Is Featured"),
        default=False,
    )
    is_active = models.BooleanField(
        _("Is Active"),
        default=True,
    )
    created_at = models.DateTimeField(
        _("Created At"),
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        _("Updated At"),
        auto_now=True,
    )

    def __str__(self):
        return self.name
    
class BusinessImage(models.Model):
    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name='gallery_images',
        verbose_name=_("Business"),
    )
    image = models.ImageField(
        _("Image"),
        upload_to='business_images/',
    )
    uploaded_at = models.DateTimeField(
        _("Uploaded At"),
        auto_now_add=True,
    )

    def __str__(self):
        return f"Image for {self.business.name}"
    
    class Meta:
        verbose_name = _("Business Image")
        verbose_name_plural = _("Business Images")

class BusinessReview(models.Model):
    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name=_("Business"),
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='business_reviews',
        verbose_name=_("User"),
    )
    rating = models.PositiveSmallIntegerField(
        _("Rating"),
    )
    comment = models.TextField(
        _("Comment"),
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(
        _("Created At"),
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        _("Updated At"),
        auto_now=True,
    )

    def __str__(self):
        return f"Review by {self.user.username} for {self.business.name}"

    class Meta:
        verbose_name = _("Business Review")
        verbose_name_plural = _("Business Reviews")
        unique_together = ('business', 'user')

class BusinessOffer(models.Model):
    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name='offers',
        verbose_name=_("Business"),
    )
    coupon_code = models.CharField(
        _("Coupon Code"),
        max_length=50,
        null=True,
        blank=True,
    )
    title = models.CharField(
        _("Offer Title"),
        max_length=255,
    )
    description = models.TextField(
        _("Offer Description"),
    )
    start_date = models.DateTimeField(
        _("Start Date"),
    )
    end_date = models.DateTimeField(
        _("End Date"),
    )
    is_popular = models.BooleanField(
        _("Is Popular"),
        default=False,
    )
    is_active = models.BooleanField(
        _("Is Active"),
        default=True,
    )
    created_at = models.DateTimeField(
        _("Created At"),
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        _("Updated At"),
        auto_now=True,
    )

    def __str__(self):
        return f"Offer: {self.title} for {self.business.name}"
    
    class Meta:
        verbose_name = _("Business Offer")
        verbose_name_plural = _("Business Offers")


class RedeemedOffer(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='redeemed_offers',
        verbose_name=_("User"),
    )
    offer = models.ForeignKey(
        BusinessOffer,
        on_delete=models.CASCADE,
        related_name='redeemed_by',
        verbose_name=_("Offer"),
    )
    redeemed_at = models.DateTimeField(
        _("Redeemed At"),
        auto_now_add=True,
    )

    is_used = models.BooleanField(
        _("Is Used"),
        default=True,
    )

    def __str__(self):
        return f"{self.user.username} redeemed {self.offer.title}"

    class Meta:
        verbose_name = _("Redeemed Offer")
        verbose_name_plural = _("Redeemed Offers")
        unique_together = ('user', 'offer')