from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from datetime import timedelta
import tempfile
from .models import TempFile, DownloadLog

class TempFileModelTest(TestCase):
    def setUp(self):
        self.temp_file = TempFile.objects.create(
            original_filename="test.txt",
            file_size=1024,
            file_hash="abcd1234",
            expiry_minutes=60
        )
    
    def test_is_expired(self):
        # Test non-expired file
        self.assertFalse(self.temp_file.is_expired())
        
        # Test expired file
        self.temp_file.expires_at = timezone.now() - timedelta(minutes=1)
        self.temp_file.save()
        self.assertTrue(self.temp_file.is_expired())
    
    def test_can_download(self):
        self.assertTrue(self.temp_file.can_download())
        
        # Test max downloads reached
        self.temp_file.download_count = self.temp_file.max_downloads
        self.temp_file.save()
        self.assertFalse(self.temp_file.can_download())

class FileUploadTest(TestCase):
    def setUp(self):
        self.client = Client()
    
    def test_upload_file(self):
        test_file = SimpleUploadedFile(
            "test.txt", 
            b"test content",
            content_type="text/plain"
        )
        
        response = self.client.post(reverse('home'), {
            'file': test_file,
            'expiry_minutes': 60,
            'max_downloads': 50
        })
        
        self.assertEqual(response.status_code, 302)  # Redirect after successful upload
        self.assertTrue(TempFile.objects.filter(original_filename="test.txt").exists())
    
    # def test_file_download(self):
    #     # Create test file
    #     with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
    #         tmp_file.write(b"test content")
    #         tmp_file_path = tmp_file.name
        
    #     temp_file = TempFile.objects.create(
    #         original_filename="test.txt",
    #         file_size=12,
    #         file_hash="abcd1234",
    #         expiry_minutes=60
    #     )
    #     temp_file.file.name = tmp_file_path
    #     temp_file.save()
        
    #     response = self.client.get(reverse('download_file', args=[temp_file.share_token]))
    #     self.assertEqual(response.status_code, 200)
    #     self.assertEqual(response.content, b"test content")

    def test_file_download(self):
        # ایجاد یک فایل تستی با SimpleUploadedFile
        test_file = SimpleUploadedFile(
            "test.txt",
            b"test content",
            content_type="text/plain"
        )
        
        # ایجاد TempFile واقعی با فایل bind شده
        temp_file = TempFile.objects.create(
            original_filename="test.txt",
            file_size=test_file.size,
            file_hash="abcd1234",
            expiry_minutes=60,
            file=test_file,  # مهم: فایل واقعی به مدل متصل می‌شود
            is_active=True
        )
        
        # اطمینان از اینکه فایل هنوز منقضی نشده
        temp_file.expires_at = temp_file.created_at + timezone.timedelta(minutes=60)
        temp_file.save()
        
        # فراخوانی view دانلود
        response = self.client.get(reverse('download_file', args=[temp_file.share_token]))
        
        # بررسی status code و محتوا
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"test content")

class APITest(TestCase):
    def setUp(self):
        self.client = Client()
        self.temp_file = TempFile.objects.create(
            original_filename="test.txt",
            file_size=1024,
            file_hash="abcd1234",
            expiry_minutes=60
        )
    
    def test_file_status_api(self):
        response = self.client.get(reverse('api_file_status', args=[self.temp_file.share_token]))
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['data']['filename'], 'test.txt')
    
    def test_health_check(self):
        response = self.client.get(reverse('health_check'))
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data['status'], 'healthy')
