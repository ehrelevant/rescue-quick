from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('feed/', views.feed, name='feed'),
    path('feed/<int:pair_id>/', views.feed, name='feed'),
    path('api/sensor-data/<int:pair_id>/', views.post_sensor_data, name='sensor_data'),
    path('api/get-flood-status/', views.get_flood_status, name='get_flood_status'),
    path('api/upload-image/<int:pair_id>', views.post_image, name='upload_image'),
    path(
        'api/post-cam-health/<int:pair_id>',
        views.post_cam_health,
        name='post_cam_health',
    ),
    path('api/signal-rescue', views.signal_rescue, name='signal_rescue'),
    path('configure/', views.list_monitors, name='list_monitors'),
    path('configure/<int:pair_id>/', views.configure_monitor),
    path('configure/new/', views.new_monitor),
]
