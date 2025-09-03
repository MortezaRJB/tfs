from django.conf import settings
import os

class AppConfig:
    # File upload settings
    MAX_FILE_SIZE = getattr(settings, 'MAX_FILE_SIZE', 10 * 1024 * 1024)  # 10MB
    ALLOWED_EXTENSIONS = getattr(settings, 'ALLOWED_EXTENSIONS', [
        'txt', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',
        'jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg',
        'mp3', 'mp4', 'avi', 'mov', 'wmv',
        'zip', 'rar', '7z', 'tar', 'gz'
    ])
    
    # Security settings
    SCAN_UPLOADED_FILES = getattr(settings, 'SCAN_UPLOADED_FILES', True)
    RESTRICT_TO_UPLOAD_IP = getattr(settings, 'RESTRICT_TO_UPLOAD_IP', False)
    ENABLE_PASSWORD_PROTECTION = getattr(settings, 'ENABLE_PASSWORD_PROTECTION', False)
    
    # Performance settings
    ENABLE_CDN = getattr(settings, 'ENABLE_CDN', False)
    CDN_URL = getattr(settings, 'CDN_URL', '')
    ENABLE_COMPRESSION = getattr(settings, 'ENABLE_COMPRESSION', True)
    
    # Cleanup settings
    AUTO_CLEANUP_INTERVAL = getattr(settings, 'AUTO_CLEANUP_INTERVAL', 5)  # minutes
    KEEP_INACTIVE_FILES_DAYS = getattr(settings, 'KEEP_INACTIVE_FILES_DAYS', 7)
    
    # Rate limiting
    MAX_UPLOADS_PER_HOUR = getattr(settings, 'MAX_UPLOADS_PER_HOUR', 1000)
    MAX_DOWNLOADS_PER_HOUR = getattr(settings, 'MAX_DOWNLOADS_PER_HOUR', 50000)
    
    @classmethod
    def is_allowed_extension(cls, filename):
        """Check if file extension is allowed"""
        if not cls.ALLOWED_EXTENSIONS:
            return True
        
        ext = filename.split('.')[-1].lower() if '.' in filename else ''
        return ext in cls.ALLOWED_EXTENSIONS
    
    @classmethod
    def get_max_file_size_mb(cls):
        """Get max file size in MB"""
        return cls.MAX_FILE_SIZE / (1024 * 1024)
