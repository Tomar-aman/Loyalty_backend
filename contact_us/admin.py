from django.contrib import admin
from .models import ContactUsMessage, FAQ, Support, SubsciberEmail, Address, SocialMediaLink, APPDownloadLink, LandingPageContent

@admin.register(Support)
class SupportAdmin(admin.ModelAdmin):
    list_display = ('country_code', 'phone_number', 'email', 'created_at', 'updated_at')
    search_fields = ('country_code', 'phone_number', 'email')

@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ('question', 'is_active', 'created_at', 'updated_at')
    search_fields = ('question',)
    list_filter = ('is_active',)

@admin.register(ContactUsMessage)
class ContactUsMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'is_resolved', 'created_at', 'updated_at')
    search_fields = ('name', 'email', 'subject')
    list_filter = ('is_resolved',)

@admin.register(SubsciberEmail)
class SubscriberEmailAdmin(admin.ModelAdmin):
    list_display = ('email', 'created_at', 'updated_at')
    search_fields = ('email',)

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('city', 'state', 'country', 'postal_code', 'created_at', 'updated_at')
    search_fields = ('address_line_1', 'address_line_2', 'city', 'state', 'country', 'postal_code')

@admin.register(SocialMediaLink)
class SocialMediaLinkAdmin(admin.ModelAdmin):
    list_display = ('instagram', 'facebook', 'twitter', 'created_at', 'updated_at')
    search_fields = ('instagram', 'facebook', 'twitter')

@admin.register(APPDownloadLink)
class APPDownloadLinkAdmin(admin.ModelAdmin):
    list_display = ('android_link', 'ios_link', 'created_at', 'updated_at')

@admin.register(LandingPageContent)
class LandingPageContentAdmin(admin.ModelAdmin):
    list_display = ('id', 'created_at', 'updated_at')