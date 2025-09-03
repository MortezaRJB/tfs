import hashlib
import hmac
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

class FileSecurityManager:
    @staticmethod
    def generate_secure_token(file_id, timestamp=None):
        """Generate cryptographically secure token"""
        if timestamp is None:
            timestamp = timezone.now().timestamp()
        
        message = f"{file_id}:{timestamp}"
        signature = hmac.new(
            settings.SECRET_KEY.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return f"{signature[:16]}"
    
    @staticmethod
    def verify_file_access(request, temp_file):
        """Verify if user can access file"""
        # Check IP restrictions if needed
        if hasattr(settings, 'RESTRICT_TO_UPLOAD_IP') and settings.RESTRICT_TO_UPLOAD_IP:
            client_ip = FileSecurityManager.get_client_ip(request)
            if temp_file.ip_address and temp_file.ip_address != client_ip:
                return False, "Access denied from this IP"
        
        # Check time-based restrictions
        if temp_file.is_expired():
            return False, "File has expired"
        
        # Check download limits
        if temp_file.download_count >= temp_file.max_downloads:
            return False, "Download limit reached"
        
        return True, "Access granted"
    
    @staticmethod
    def get_client_ip(request):
        """Get real client IP"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    @staticmethod
    def scan_file_content(file_path):
        """Basic file content scanning"""
        dangerous_patterns = [
            b'<script',
            b'javascript:',
            b'<?php',
            b'<%',
            b'eval(',
        ]
        
        try:
            with open(file_path, 'rb') as f:
                content = f.read(1024 * 10)  # Read first 10KB
                content_lower = content.lower()
                
                for pattern in dangerous_patterns:
                    if pattern in content_lower:
                        return False, f"Potentially dangerous content detected"
            
            return True, "File appears safe"
        except Exception as e:
            return False, f"Error scanning file: {str(e)}"

