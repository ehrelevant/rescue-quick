from django.contrib import admin

from .models import CameraLogs, SensorLogs, SensorCamera

admin.site.register(CameraLogs)
admin.site.register(SensorLogs)
admin.site.register(SensorCamera)
