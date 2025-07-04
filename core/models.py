from django.db import models

from storages.backends.s3boto3 import S3Boto3Storage
from django.utils import timezone

from datetime import datetime
import pytz


class CameraImageStorage(S3Boto3Storage):
    location = 'camera'
    file_overwrite = False


class CameraImageProcessedStorage(S3Boto3Storage):
    location = 'processed'
    file_overwrite = False


def elapsed_time(timestamp: datetime | None) -> str:
    if not timestamp:
        return 'N/A'

    delta = timezone.now() - timestamp
    s = delta.seconds
    d = delta.days
    if d == 1:
        return '1 day ago'
    elif d > 1 and d <= 30:
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
        mins = (s-3600)//60
        mins_text = f"{mins} mins " if mins > 1 else ""
        return f'1 hr {mins_text}ago'
    elif d == 0 and s < 86400:
        hours = s//3600
        mins = (s - 3600*hours) // 60
        mins_text = f"{mins} mins " if mins > 1 else ""
        return f'{hours} hrs {mins_text}ago'
    else:
        proper_time = timestamp.astimezone(pytz.timezone('Asia/Hong_Kong'))
        return proper_time.strftime(r'on %Y/%m/%d')


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
    location = models.TextField()
    monitor_state = models.CharField(choices=MonitorState, default=MonitorState.SAFE)

    # sensor
    flood_number = models.IntegerField(default=1)
    current_depth = models.FloatField(null=True)
    threshold_depth = models.FloatField(default=1)
    is_wet = models.BooleanField(default=False)

    # camera
    person_count = models.IntegerField(default=0)
    dog_count = models.IntegerField(default=0)
    cat_count = models.IntegerField(default=0)

    # timestamps
    timestamp = models.DateTimeField(auto_now=True)
    state_change_timestamp = models.DateTimeField(default=timezone.now)
    last_sensor_report = models.DateTimeField(null=True)
    last_camera_report = models.DateTimeField(null=True)

    # auth token
    token = models.CharField(
        max_length=128,
        unique=True,
        blank=True,
        null=True,
    )

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


class RescuerContacts(models.Model):
    email_addr = models.EmailField(unique=True)
    devices = models.ManyToManyField(SensorCamera, related_name='devices')
