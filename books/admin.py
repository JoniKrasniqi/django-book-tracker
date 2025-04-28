from django.contrib import admin
from .models import Book

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'price', 'stock', 'upc', 'reviews', 'created_by', 'source', 'created_at')
    list_filter = ('source', 'created_by')
    search_fields = ('title', 'description', 'upc')
    readonly_fields = ('created_at', 'updated_at')
