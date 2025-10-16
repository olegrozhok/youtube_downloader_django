from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('formats/', views.get_formats, name='get_formats'),
    path('progress/<str:task_id>/', views.get_progress, name='get_progress'),
    path('download/<str:task_id>/', views.download_file, name='download_file'),
]
