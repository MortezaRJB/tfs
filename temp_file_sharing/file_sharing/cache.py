from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from django.utils import timezone
from .models import TempFile
import json
import hashlib

class FileCache:
    @staticmethod
    def get_file_info(token):
        """Get cached file info"""
        cache_key = f"temp_file_info_{token}"
        return cache.get(cache_key)
    
    @staticmethod
    def set_file_info(temp_file, timeout=None):
        """Cache file info"""
        if timeout is None:
            timeout = (temp_file.expires_at - timezone.now()).total_seconds()
        
        cache_key = f"temp_file_info_{temp_file.share_token}"
        file_data = {
            'id': str(temp_file.id),
            'filename': temp_file.original_filename,
            'size': temp_file.file_size,
            'expires_at': temp_file.expires_at.isoformat(),
            'download_count': temp_file.download_count,
            'max_downloads': temp_file.max_downloads,
            'is_active': temp_file.is_active,
        }
        
        cache.set(cache_key, file_data, timeout=int(timeout))
        return file_data
    
    @staticmethod
    def increment_download_count(token):
        """Atomically increment download count in cache"""
        cache_key = f"temp_file_info_{token}"
        file_data = cache.get(cache_key)
        
        if file_data:
            file_data['download_count'] += 1
            cache.set(cache_key, file_data, timeout=cache.ttl(cache_key))
        
        return file_data
    
    @staticmethod
    def invalidate_file_cache(token):
        """Remove file from cache"""
        cache_key = f"temp_file_info_{token}"
        cache.delete(cache_key)
    
    @staticmethod
    def cache_file_stats():
        """Cache system statistics"""
        stats = {
            'total_files': TempFile.objects.count(),
            'active_files': TempFile.objects.filter(
                is_active=True,
                expires_at__gt=timezone.now()
            ).count(),
            'expired_files': TempFile.objects.filter(
                expires_at__lt=timezone.now()
            ).count(),
            'total_downloads': sum(
                TempFile.objects.values_list('download_count', flat=True)
            ),
            'cached_at': timezone.now().isoformat()
        }
        
        cache.set('system_stats', stats, timeout=300)  # Cache for 5 minutes
        return stats

