from django.contrib import admin
from .models import User, OTP, Country, City, UserSearchHistory

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


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')
    search_fields = ('name', 'code')
    ordering = ('name',)

@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ('name', 'country')
    search_fields = ('name', 'country__name')
    ordering = ('name',)

@admin.register(UserSearchHistory)
class UserSearchHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'search', 'searched_at')
    search_fields = ('user__email', 'search')
    ordering = ('-searched_at',)