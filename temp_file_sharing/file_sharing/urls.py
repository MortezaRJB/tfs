from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('file/<str:token>/', views.file_info, name='file_info'),
    path('download/<str:token>/', views.download_file, name='download_file'),
    path('api/status/<str:token>/', views.api_file_status, name='api_file_status'),
    path('admin/cleanup/', views.cleanup_view, name='cleanup'),
    path('health/', views.health_check, name='health_check'),
]