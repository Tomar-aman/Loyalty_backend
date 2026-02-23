from django.contrib import admin
from .models import NewsArticle

@admin.register(NewsArticle)
class NewsArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'city', 'published_at', 'id')
    list_filter = ('category', 'city', 'published_at')
    search_fields = ('title', 'content')
    readonly_fields = ('published_at',)
    ordering = ('-published_at',)
    
    fieldsets = (
        ('Article Information', {
            'fields': ('title', 'content', 'icon')
        }),
        ('Location & Category', {
            'fields': ('category', 'city')
        }),
        ('Publishing Details', {
            'fields': ('published_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('category', 'city')

# Register your models here.
