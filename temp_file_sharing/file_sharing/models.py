from django.db import models
from django.utils import timezone
from datetime import timedelta
import uuid
import hashlib

class TempFile(models.Model):
    EXPIRY_CHOICES = [
        (5, '5 دقیقه'),
        (30, '30 دقیقه'),
        (60, '1 ساعت'),
        # (360, '6 ساعت'),
        # (720, '12 ساعت'),
        # (1440, '24 ساعت'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.FileField(upload_to='temp_files/')
    original_filename = models.CharField(max_length=255)
    file_size = models.BigIntegerField()
    file_hash = models.CharField(max_length=64, unique=True)
    share_token = models.CharField(max_length=32, unique=True)
    
    expiry_minutes = models.IntegerField(choices=EXPIRY_CHOICES, default=60)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    download_count = models.IntegerField(default=0)
    max_downloads = models.IntegerField(default=100)
    
    is_active = models.BooleanField(default=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        db_table = 'temp_files'
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=self.expiry_minutes)
        
        if not self.share_token:
            self.share_token = self.generate_share_token()
            
        super().save(*args, **kwargs)
    
    def generate_share_token(self):
        """Generate unique share token"""
        unique_string = f"{self.id}{timezone.now().isoformat()}"
        return hashlib.md5(unique_string.encode()).hexdigest()[:16]
    
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    def can_download(self):
        return (self.is_active and 
                not self.is_expired() and 
                self.download_count < self.max_downloads)
    
    def get_share_url(self, request=None):
        if request:
            return request.build_absolute_uri(f'/file/{self.share_token}/')
        return f'/file/{self.share_token}/'
    
    def get_file_extension(self):
        return self.original_filename.split('.')[-1] if '.' in self.original_filename else ''
    
    def get_human_readable_size(self):
        """Convert bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if self.file_size < 1024:
                return f"{self.file_size:.1f} {unit}"
            self.file_size /= 1024
        return f"{self.file_size:.1f} TB"
    
    def __str__(self):
        return f"{self.original_filename} - {self.share_token}"

class DownloadLog(models.Model):
    temp_file = models.ForeignKey(TempFile, on_delete=models.CASCADE, related_name='download_logs')
    downloaded_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    success = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'download_logs'
        ordering = ['-downloaded_at']

