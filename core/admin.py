from django.contrib import admin

from .models import CameraLogs, SensorLogs, SensorCamera, RescuerContacts

admin.site.register(CameraLogs)
admin.site.register(SensorLogs)
admin.site.register(SensorCamera)
admin.site.register(RescuerContacts)
