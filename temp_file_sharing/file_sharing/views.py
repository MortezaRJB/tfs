from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.utils import timezone
from django.core.cache import cache
from django.db.models import F
from django.urls import reverse
import hashlib
import mimetypes
import os
from .models import TempFile, DownloadLog
from .forms import FileUploadForm
from .tasks import cleanup_expired_files

def home(request):
    """Home page with upload form"""
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            temp_file = form.save(commit=False)
            
            # Set file metadata
            uploaded_file = form.cleaned_data['file']
            temp_file.original_filename = uploaded_file.name
            temp_file.file_size = uploaded_file.size
            
            # Generate file hash
            file_content = uploaded_file.read()
            temp_file.file_hash = hashlib.sha256(file_content).hexdigest()
            uploaded_file.seek(0)  # Reset file pointer

            # bind file to model again (خیلی مهم)
            temp_file.file = uploaded_file 
            
            # Set user info
            temp_file.ip_address = get_client_ip(request)
            temp_file.user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            temp_file.save()
            
            # Cache file info for quick access
            cache.set(f'temp_file_{temp_file.share_token}', {
                'id': str(temp_file.id),
                'filename': temp_file.original_filename,
                'size': temp_file.file_size,
                'expires_at': temp_file.expires_at.isoformat(),
                'download_count': temp_file.download_count,
                'max_downloads': temp_file.max_downloads
            }, timeout=temp_file.expiry_minutes * 60)
            
            messages.success(request, 'فایل با موفقیت آپلود شد!')
            return redirect('file_info', token=temp_file.share_token)
        # else:
        #     print("❌ فرم نامعتبره:", form.errors)
    else:
        form = FileUploadForm()
    
    # Get recent files stats
    total_files = TempFile.objects.filter(is_active=True).count()
    active_files = TempFile.objects.filter(
        is_active=True,
        expires_at__gt=timezone.now()
    ).count()
    
    context = {
        'form': form,
        'total_files': total_files,
        'active_files': active_files,
    }
    return render(request, 'file_sharing/home.html', context)

def file_info(request, token):
    """Show file information and download link"""
    temp_file = get_object_or_404(TempFile, share_token=token, is_active=True)
    
    if temp_file.is_expired():
        messages.error(request, 'این فایل منقضی شده است.')
        return render(request, 'file_sharing/expired.html', {'temp_file': temp_file})
    
    context = {
        'temp_file': temp_file,
        'share_url': temp_file.get_share_url(request),
        'time_remaining': temp_file.expires_at - timezone.now(),
        'download_percentage': (temp_file.download_count / temp_file.max_downloads) * 100,
    }
    return render(request, 'file_sharing/file_info.html', context)

def download_file(request, token):
    """Handle file download"""
    temp_file = get_object_or_404(TempFile, share_token=token, is_active=True)
    
    # Check if file can be downloaded
    if not temp_file.can_download():
        if temp_file.is_expired():
            return render(request, 'file_sharing/expired.html', {'temp_file': temp_file})
        else:
            messages.error(request, 'حداکثر تعداد دانلود برای این فایل تکمیل شده است.')
            return redirect('file_info', token=token)
    
    try:
        # Increment download count atomically
        TempFile.objects.filter(id=temp_file.id).update(
            download_count=F('download_count') + 1
        )
        
        # Log download
        DownloadLog.objects.create(
            temp_file=temp_file,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            success=True
        )
        
        # Prepare file response
        file_path = temp_file.file.path
        if os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                content_type, _ = mimetypes.guess_type(file_path)
                response = HttpResponse(f.read(), content_type=content_type or 'application/octet-stream')
                response['Content-Disposition'] = f'a50ttachment; filename="{temp_file.original_filename}"'
                response['Content-Length'] = temp_file.file_size
                return response
        else:
            raise Http404("فایل یافت نشد")
            
    except Exception as e:
        # Log failed download
        DownloadLog.objects.create(
            temp_file=temp_file,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            success=False
        )
        messages.error(request, 'خطا در دانلود فایل. لطفاً دوباره تلاش کنید.')
        return redirect('file_info', token=token)

@require_http_methods(["GET"])
def api_file_status(request, token):
    """API endpoint to check file status"""
    try:
        # Try cache first
        cached_info = cache.get(f'temp_file_{token}')
        if cached_info:
            temp_file_data = cached_info
            expires_at = timezone.datetime.fromisoformat(cached_info['expires_at'])
            is_expired = timezone.now() > expires_at
        else:
            # Fallback to database
            temp_file = get_object_or_404(TempFile, share_token=token, is_active=True)
            temp_file_data = {
                'id': str(temp_file.id),
                'filename': temp_file.original_filename,
                'size': temp_file.file_size,
                'expires_at': temp_file.expires_at.isoformat(),
                'download_count': temp_file.download_count,
                'max_downloads': temp_file.max_downloads
            }
            is_expired = temp_file.is_expired()
        
        return JsonResponse({
            'status': 'success',
            'data': {
                **temp_file_data,
                'is_expired': is_expired,
                'downloads_remaining': temp_file_data['max_downloads'] - temp_file_data['download_count'],
                'size_human': format_file_size(temp_file_data['size'])
            }
        })
    except TempFile.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'فایل یافت نشد'}, status=404)

def cleanup_view(request):
    """Trigger manual cleanup (admin only)"""
    if not request.user.is_staff:
        return JsonResponse({'status': 'error', 'message': 'دسترسی مجاز نیست'}, status=403)
    
    # Trigger cleanup task
    result = cleanup_expired_files.delay()
    
    return JsonResponse({
        'status': 'success',
        'message': 'پروسه پاکسازی شروع شد',
        'task_id': result.id
    })

def health_check(request):
    """Health check endpoint for load balancer"""
    try:
        # Check database connection
        TempFile.objects.count()
        
        # Check cache connection
        cache.set('health_check', 'ok', timeout=10)
        cache.get('health_check')
        
        return JsonResponse({
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'services': {
                'database': 'ok',
                'cache': 'ok'
            }
        })
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'error': str(e)
        }, status=500)

def get_client_ip(request):
    """Get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def format_file_size(size_bytes):
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0B"
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names)-1:
        size_bytes /= 1024
        i += 1
    return f"{size_bytes:.1f}{size_names[i]}"



