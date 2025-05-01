from django.db import models

from storages.backends.s3boto3 import S3Boto3Storage
from django.utils import timezone


class CameraImageStorage(S3Boto3Storage):
    location = 'camera'
    file_overwrite = False


class CameraImageProcessedStorage(S3Boto3Storage):
    location = 'processed'
    file_overwrite = False


class SensorCamera(models.Model):
    class MonitorState(models.TextChoices):
        DANGEROUS = 'Dangerous'
        CAUTION = 'Caution'
        SAFE = 'Safe'

    pair_id = models.IntegerField(primary_key=True)
    pair_name = models.CharField()
    current_depth = models.FloatField(null=True)
    threshold_depth = models.FloatField(default=1)
    location = models.TextField()
    flood_number = models.IntegerField(default=1)
    timestamp = models.DateTimeField(auto_now=True)
    monitor_state = models.CharField(
        choices=MonitorState, default=MonitorState.SAFE
    )
    state_change_timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f'{self.location}: Time {self.timestamp} - Depth {self.current_depth}'


class CameraLogs(models.Model):
    camera_id = models.ForeignKey(SensorCamera, on_delete=models.CASCADE)
    flood_number = models.IntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)
    person_count = models.IntegerField(default=0)
    pet_count = models.IntegerField(default=0)
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
