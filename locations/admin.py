from django.contrib import admin
from .models import Category, Location

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'created_at')
    search_fields = ('name',)

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'author', 'is_deleted', 'created_at')
    list_filter = ('is_deleted', 'category', 'created_at')
    search_fields = ('title', 'address')