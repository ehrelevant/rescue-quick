from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('feed/<int:monitor_id>/', views.feed, name='feed'),
    path('api/sensor-data/', views.post_sensor_data, name='sensor_data'),
]
