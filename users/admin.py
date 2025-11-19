from django.contrib import admin
from .models import User, OTP

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'is_active', 'is_admin', 'is_superadmin')
    search_fields = ('email', 'first_name', 'last_name')
    list_filter = ('is_active', 'is_admin', 'is_superadmin')
    ordering = ('email',)

@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    list_display = ('user', 'otp_code', 'created_at', 'expires_at')
    search_fields = ('user__email', 'otp_code')
    list_filter = ('expires_at', 'created_at')
    ordering = ('-created_at',)