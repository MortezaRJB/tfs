import os
from celery import shared_task
from django.utils import timezone
from django.core.cache import cache
from django.conf import settings
from .models import TempFile

@shared_task
def cleanup_expired_files():
    """Clean up expired files from database and storage"""
    expired_files = TempFile.objects.filter(
        expires_at__lt=timezone.now(),
        is_active=True
    )
    
    deleted_count = 0
    for temp_file in expired_files:
        try:
            # Delete physical file
            if temp_file.file and os.path.exists(temp_file.file.path):
                os.remove(temp_file.file.path)
            
            # Remove from cache
            cache.delete(f'temp_file_{temp_file.share_token}')
            
            # Mark as inactive instead of deleting (for analytics)
            temp_file.is_active = False
            temp_file.save()
            
            deleted_count += 1
        except Exception as e:
            print(f"Error deleting file {temp_file.id}: {e}")
    
    return f"Cleaned up {deleted_count} expired files"

@shared_task
def cleanup_old_inactive_files():
    """Clean up old inactive files (older than 7 days)"""
    old_date = timezone.now() - timezone.timedelta(days=7)
    old_files = TempFile.objects.filter(
        is_active=False,
        created_at__lt=old_date
    )
    
    deleted_count = old_files.count()
    old_files.delete()
    
    return f"Permanently deleted {deleted_count} old files"



