from django.db import models

from storages.backends.s3boto3 import S3Boto3Storage
from django.utils import timezone

from datetime import datetime

class CameraImageStorage(S3Boto3Storage):
    location = 'camera'
    file_overwrite = False


class CameraImageProcessedStorage(S3Boto3Storage):
    location = 'processed'
    file_overwrite = False

def elapsed_time(timestamp: datetime) -> str:
        delta = timezone.now() - timestamp
        s = delta.seconds
        d = delta.days
        if d == 1:
            return '1 day ago'
        elif d > 1:
            return f'{d} days ago'
        elif d == 0 and s <= 1:
            return 'Just now'
        elif d == 0 and s < 60:
            return f'{s} seconds ago'
        elif d == 0 and s < 120:
            return '1 minute ago'
        elif d == 0 and s < 3600:
            return f'{s // 60} minutes ago'
        elif d == 0 and s < 7200:
            return '1 hour ago'
        elif d == 0 and s < 86400:
            return f'{s // 3600} hours ago'
        else:
            return timestamp.strftime(r'on %Y/%m/%d')

class SensorCamera(models.Model):
    class MonitorState(models.TextChoices):
        DANGEROUS = 'Dangerous'
        CAUTION = 'Caution'
        SAFE = 'Safe'
        UNRESPONSIVE_SENSOR = 'Unresponsive Sensor'
        UNRESPONSIVE_CAMERA = 'Unresponsive Camera'
        UNRESPONSIVE_BOTH = 'Both Unresponsive'
    
    pair_id = models.IntegerField(primary_key=True)
    pair_name = models.CharField()
    current_depth = models.FloatField(null=True)
    threshold_depth = models.FloatField(default=1)
    location = models.TextField()
    flood_number = models.IntegerField(default=1)
    person_count = models.IntegerField(default=0)
    dog_count = models.IntegerField(default=0)
    cat_count = models.IntegerField(default=0)
    timestamp = models.DateTimeField(auto_now=True)
    monitor_state = models.CharField(choices=MonitorState, default=MonitorState.SAFE)
    # Remove state_change_timestamp
    state_change_timestamp = models.DateTimeField(default=timezone.now)
    last_sensor_report = models.DateTimeField(default=timezone.now)
    last_camera_report = models.DateTimeField(default=timezone.now)

    @property
    def is_long_time(self) -> bool:
        # Checks if at least an hour has passed
        delta = timezone.now() - self.state_change_timestamp
        return delta.seconds >= 3600

    def __str__(self):
        return f'{self.location}: Time {self.timestamp} - Depth {self.current_depth}'


class CameraLogs(models.Model):
    camera_id = models.ForeignKey(SensorCamera, on_delete=models.CASCADE)
    flood_number = models.IntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)
    person_count = models.IntegerField(default=0)
    dog_count = models.IntegerField(default=0)
    cat_count = models.IntegerField(default=0)
    image = models.ImageField(storage=CameraImageStorage)
    image_processed = models.ImageField(storage=CameraImageProcessedStorage)

    @property
    def raw_image_url(self) -> str:
        storage = CameraImageProcessedStorage()
        return storage.url(self.image_processed.name)

    @property
    def processed_image_url(self) -> str:
        storage = CameraImageProcessedStorage()
        return storage.url(self.image_processed.name)

    def __str__(self):
        return f'Camera {self.camera_id}'


class SensorLogs(models.Model):
    sensor_id = models.ForeignKey(SensorCamera, on_delete=models.CASCADE)
    depth = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)
    flood_number = models.IntegerField()

    def __str__(self):
        return f'Sensor {self.sensor_id}'
