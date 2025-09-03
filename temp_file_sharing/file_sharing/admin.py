from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import TempFile, DownloadLog

@admin.register(TempFile)
class TempFileAdmin(admin.ModelAdmin):
    list_display = ['original_filename', 'file_size_display', 'share_token', 'download_count', 
                   'max_downloads', 'created_at', 'expires_at', 'is_active', 'status_display']
    list_filter = ['is_active', 'created_at', 'expiry_minutes']
    search_fields = ['original_filename', 'share_token', 'file_hash']
    readonly_fields = ['id', 'file_hash', 'share_token', 'created_at', 'share_url_display']
    ordering = ['-created_at']
    
    def file_size_display(self, obj):
        return obj.get_human_readable_size()
    file_size_display.short_description = 'اندازه فایل'
    
    def status_display(self, obj):
        if not obj.is_active:
            return format_html('<span style="color: red;">غیرفعال</span>')
        elif obj.is_expired():
            return format_html('<span style="color: orange;">منقضی شده</span>')
        else:
            return format_html('<span style="color: green;">فعال</span>')
    status_display.short_description = 'وضعیت'
    
    def share_url_display(self, obj):
        if obj.pk:
            url = reverse('file_info', args=[obj.share_token])
            return format_html('<a href="{}" target="_blank">{}</a>', url, url)
        return '-'
    share_url_display.short_description = 'لینک اشتراک'

@admin.register(DownloadLog)
class DownloadLogAdmin(admin.ModelAdmin):
    list_display = ['temp_file', 'downloaded_at', 'ip_address', 'success']
    list_filter = ['success', 'downloaded_at']
    search_fields = ['temp_file__original_filename', 'ip_address']
    readonly_fields = ['temp_file', 'downloaded_at', 'ip_address', 'user_agent', 'success']
    ordering = ['-downloaded_at']



