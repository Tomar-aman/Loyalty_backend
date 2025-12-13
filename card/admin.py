from django.contrib import admin
from .models import Card, CardBenefit, UserCard, UserCardHistory

class CardBenefitInline(admin.TabularInline):
    model = CardBenefit
    extra = 1

@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'duration', 'price', 'is_active', 'created_at', 'updated_at')
    search_fields = ('name',)
    list_filter = ('is_active', 'duration')
    inlines = [CardBenefitInline]

@admin.register(CardBenefit)
class CardBenefitAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'card')
    search_fields = ('title', 'card__name')
    list_filter = ('card',)

@admin.register(UserCard)
class UserCardAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'card', 'start_at', 'end_at', 'is_active', 'created_at', 'updated_at')
    search_fields = ('user__first_name', 'card__name')
    list_filter = ('is_active', 'card')

@admin.register(UserCardHistory)
class UserCardHistoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'card', 'action', 'start_at', 'end_at', 'created_at')
    search_fields = ('user__first_name', 'card__name', 'action')
    list_filter = ('action', 'card')