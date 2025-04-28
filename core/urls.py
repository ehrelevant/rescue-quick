from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('feed/<int:monitor_id>/', views.feed, name='feed'),
    path('api/sensor-data/', views.post_sensor_data, name='sensor_data'),
    path('api/get-flood-status/', views.get_flood_status, name='get_flood_status'),
    path('api/upload-image/<str:pair_id>', views.post_image, name='upload_image'),
]
