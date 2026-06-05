from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import BookRelation


@admin.register(BookRelation)
class BookRelationAdmin(admin.ModelAdmin):
    list_display = [
        'source_book_link',
        'target_book_link',
        'relation_type',
        'weight',
        'is_manual',
        'created_at'
    ]
    list_filter = ['relation_type', 'is_manual', 'created_at']
    search_fields = [
        'source_book__title',
        'source_book__author',
        'target_book__title',
        'target_book__author'
    ]
    list_editable = ['weight']
    readonly_fields = ['created_at', 'updated_at']
    raw_id_fields = ['source_book', 'target_book']

    fieldsets = (
        (None, {
            'fields': ('source_book', 'target_book', 'relation_type', 'weight', 'is_manual')
        }),
        ('系统信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def source_book_link(self, obj):
        url = reverse('admin:books_book_change', args=[obj.source_book.pk])
        return format_html('<a href="{}">{}</a>', url, obj.source_book.title)
    source_book_link.short_description = '源图书'

    def target_book_link(self, obj):
        url = reverse('admin:books_book_change', args=[obj.target_book.pk])
        return format_html('<a href="{}">{}</a>', url, obj.target_book.title)
    target_book_link.short_description = '目标图书'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('source_book', 'target_book')
