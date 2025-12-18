from django.contrib import admin
from .models import Business, BusinessCategory, BusinessImage, BusinessOffer, RedeemedOffer

@admin.register(BusinessCategory)
class BusinessCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at', 'updated_at')
    search_fields = ('name',)
    list_filter = ('is_active',)


@admin.register(BusinessOffer)
class BusinessOfferAdmin(admin.ModelAdmin):
    list_display = ('title', 'business', 'start_date', 'end_date', 'is_active', 'created_at', 'updated_at')
    search_fields = ('title', 'business__name')
    list_filter = ('is_active', 'start_date', 'end_date')

class BusinessImageInline(admin.TabularInline):
    model = BusinessImage
    extra = 1


@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'category', 'is_active', 'is_featured', 'created_at', 'updated_at')
    search_fields = ('name', 'owner__username', 'category__name')
    list_filter = ('is_active', 'is_featured', 'category')
    inlines = [BusinessImageInline]

@admin.register(RedeemedOffer)
class RedeemedOfferAdmin(admin.ModelAdmin):
    list_display = ('user', 'offer', 'redeemed_at', 'is_used')
    # search_fields = ('user__username', 'offer__title')
    list_filter = ('is_used', 'redeemed_at')