from django.contrib import admin
from .models import SMTPSettings, FirebaseSettings, GoogleMapsSettings

@admin.register(SMTPSettings)
class SMTPSettingsAdmin(admin.ModelAdmin):
    list_display = ('host', 'port', 'from_email', 'use_tls', 'updated_at')
    readonly_fields = ('updated_at',)

@admin.register(FirebaseSettings)
class FirebaseSettingsAdmin(admin.ModelAdmin):
    list_display = ('id','file_name' ,'updated_at',)
    readonly_fields = ('updated_at',)

@admin.register(GoogleMapsSettings)
class GoogleMapsSettingsAdmin(admin.ModelAdmin):
    list_display = ('id','updated_at',)
    readonly_fields = ('updated_at',)