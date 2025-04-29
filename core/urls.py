from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('feed/<int:monitor_id>/', views.feed, name='feed'),
    path('api/sensor-data/', views.post_sensor_data, name='sensor_data'),
    path('api/get-flood-status/', views.get_flood_status, name='get_flood_status'),
    path('api/upload-image/<str:pair_id>', views.post_image, name='upload_image'),
    path('api/pair-id', views.get_available_pair_id, name='available_pair_id'),
    path('api/pair-id/reserve', views.post_reserve_pair_id, name='reserve_pair_id')
]
