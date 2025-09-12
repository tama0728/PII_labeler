from django.contrib import admin
from .models import Document, PIITag, PIICategory

# Register your models here.

@admin.register(PIICategory)
class PIICategoryAdmin(admin.ModelAdmin):
    list_display = ['value', 'background_color', 'description', 'created_at']
    list_filter = ['created_at']
    search_fields = ['value', 'description']
    readonly_fields = ['created_at']

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['data_id', 'number_of_subjects', 'dialog_type', 'turn_cnt', 'doc_id', 'created_by', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at', 'created_by']
    search_fields = ['data_id', 'text']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(PIITag)
class PIITagAdmin(admin.ModelAdmin):
    list_display = ['document', 'pii_category', 'tagged_text', 'confidence', 'created_by', 'created_at']
    list_filter = ['pii_category', 'confidence', 'created_at', 'created_by']
    search_fields = ['tagged_text', 'document__data_id']
    readonly_fields = ['created_at']
