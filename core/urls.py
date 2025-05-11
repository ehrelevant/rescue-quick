from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('feed/', views.feed, name='feed'),
    path('feed/<int:pair_id>/', views.feed, name='feed'),
    path('api/sensor-data/<int:pair_id>/', views.post_sensor_data, name='sensor_data'),
    path('api/get-flood-status/', views.get_flood_status, name='get_flood_status'),
    path('api/upload-image/<int:pair_id>', views.post_image, name='upload_image'),
    path('api/pair-id', views.get_available_pair_id, name='available_pair_id'),
    path('api/pair-id/reserve', views.post_reserve_pair_id, name='reserve_pair_id'),
    path('api/device-token/<int:pair_id>', views.get_device_token, name='get_device_token'),
    path(
        'api/post-cam-health/<int:pair_id>',
        views.post_cam_health,
        name='post_cam_health',
    ),
]
