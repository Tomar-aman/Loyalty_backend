from django.contrib import admin
from .models import Business, BusinessCategory, BusinessImage

@admin.register(BusinessCategory)
class BusinessCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at', 'updated_at')
    search_fields = ('name',)
    list_filter = ('is_active',)




class BusinessImageInline(admin.TabularInline):
    model = BusinessImage
    extra = 1


@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'category', 'is_active', 'is_featured', 'created_at', 'updated_at')
    search_fields = ('name', 'owner__username', 'category__name')
    list_filter = ('is_active', 'is_featured', 'category')
    inlines = [BusinessImageInline]