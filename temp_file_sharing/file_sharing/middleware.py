import time
from django.utils.deprecation import MiddlewareMixin
from django.core.cache import cache
from django.http import JsonResponse
import logging

logger = logging.getLogger(__name__)

class PerformanceMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request.start_time = time.time()
    
    def process_response(self, request, response):
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            
            # Log slow requests
            if duration > 2.0:  # More than 2 seconds
                logger.warning(f"Slow request: {request.path} took {duration:.2f}s")
            
            # Store performance metrics in cache
            cache_key = f"perf_{request.path.replace('/', '_')}"
            metrics = cache.get(cache_key, {'count': 0, 'total_time': 0, 'avg_time': 0})
            metrics['count'] += 1
            metrics['total_time'] += duration
            metrics['avg_time'] = metrics['total_time'] / metrics['count']
            cache.set(cache_key, metrics, timeout=3600)  # Store for 1 hour
            
            response['X-Response-Time'] = f"{duration:.3f}s"
        
        return response

class RateLimitMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Simple rate limiting
        client_ip = self.get_client_ip(request)
        cache_key = f"rate_limit_{client_ip}"
        
        current_requests = cache.get(cache_key, 0)
        if current_requests > 100:  # Max 100 requests per hour
            return JsonResponse(
                {'error': 'Rate limit exceeded. Try again later.'}, 
                status=429
            )
        
        cache.set(cache_key, current_requests + 1, timeout=3600)
        return None
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


