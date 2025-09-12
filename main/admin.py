from django.contrib import admin
from .models import Document, PIITag

# Register your models here.

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'created_by', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at', 'created_by']
    search_fields = ['title', 'content']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(PIITag)
class PIITagAdmin(admin.ModelAdmin):
    list_display = ['document', 'pii_type', 'tagged_text', 'confidence', 'created_by', 'created_at']
    list_filter = ['pii_type', 'confidence', 'created_at', 'created_by']
    search_fields = ['tagged_text', 'document__title']
    readonly_fields = ['created_at']
