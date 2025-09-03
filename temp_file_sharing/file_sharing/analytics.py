from django.db.models import Count, Sum, Avg
from django.utils import timezone
from datetime import timedelta
from .models import TempFile, DownloadLog
import json

class AnalyticsManager:
    @staticmethod
    def get_usage_stats(days=30):
        """Get usage statistics for specified period"""
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # File statistics
        total_files = TempFile.objects.filter(
            created_at__range=[start_date, end_date]
        ).count()
        
        active_files = TempFile.objects.filter(
            created_at__range=[start_date, end_date],
            is_active=True,
            expires_at__gt=timezone.now()
        ).count()
        
        # Download statistics
        total_downloads = DownloadLog.objects.filter(
            downloaded_at__range=[start_date, end_date],
            success=True
        ).count()
        
        # File size statistics
        size_stats = TempFile.objects.filter(
            created_at__range=[start_date, end_date]
        ).aggregate(
            total_size=Sum('file_size'),
            avg_size=Avg('file_size'),
            max_size=Max('file_size')
        )
        
        # Most popular file types
        file_types = TempFile.objects.filter(
            created_at__range=[start_date, end_date]
        ).extra(
            select={'extension': "substring(original_filename from '\\.([^\\.]*)
            ')"}
        ).values('extension').annotate(
            count=Count('extension')
        ).order_by('-count')[:10]
        
        return {
            'period': f"{days} days",
            'total_files': total_files,
            'active_files': active_files,
            'total_downloads': total_downloads,
            'download_rate': round(total_downloads / total_files, 2) if total_files > 0 else 0,
            'size_stats': size_stats,
            'popular_extensions': list(file_types),
            'generated_at': timezone.now().isoformat()
        }
    
    @staticmethod
    def get_daily_usage(days=7):
        """Get daily usage statistics"""
        daily_stats = []
        
        for i in range(days):
            date = timezone.now().date() - timedelta(days=i)
            start_time = timezone.datetime.combine(date, timezone.datetime.min.time())
            end_time = start_time + timedelta(days=1)
            
            uploads = TempFile.objects.filter(
                created_at__range=[start_time, end_time]
            ).count()
            
            downloads = DownloadLog.objects.filter(
                downloaded_at__range=[start_time, end_time],
                success=True
            ).count()
            
            daily_stats.append({
                'date': date.isoformat(),
                'uploads': uploads,
                'downloads': downloads
            })
        
        return daily_stats
    
    @staticmethod
    def get_performance_metrics():
        """Get system performance metrics"""
        # Average file lifetime
        avg_lifetime = TempFile.objects.filter(
            is_active=False,
            download_count__gt=0
        ).aggregate(
            avg_lifetime=Avg(
                timezone.now() - F('created_at'),
                output_field=DurationField()
            )
        )
        
        # Most downloaded files
        popular_files = TempFile.objects.order_by('-download_count')[:10].values(
            'original_filename', 'download_count', 'file_size', 'created_at'
        )
        
        # Error rates
        total_downloads = DownloadLog.objects.count()
        failed_downloads = DownloadLog.objects.filter(success=False).count()
        error_rate = (failed_downloads / total_downloads * 100) if total_downloads > 0 else 0
        
        return {
            'average_file_lifetime': avg_lifetime,
            'popular_files': list(popular_files),
            'error_rate': round(error_rate, 2),
            'total_download_attempts': total_downloads,
            'failed_downloads': failed_downloads
        }

