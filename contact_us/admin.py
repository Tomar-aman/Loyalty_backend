from django.contrib import admin
from .models import ContactUsMessage, FAQ, Support

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
