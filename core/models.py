from django.db import models

from storages.backends.s3boto3 import S3Boto3Storage


class CameraImageStorage(S3Boto3Storage):
    location = 'camera'
    file_overwrite = False


class SensorCamera(models.Model):
    pair_id = models.IntegerField(primary_key=True)
    current_depth = models.FloatField(null=True)
    threshold_depth = models.FloatField(default=0.5)
    location = models.TextField(null=True)
    flood_number = models.IntegerField(null=True)
    timestamp = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.location}: Time {self.timestamp} - Depth {self.current_depth}'


class CameraLogs(models.Model):
    camera_id = models.ForeignKey(SensorCamera, on_delete=models.CASCADE)
    flood_number = models.IntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(storage=CameraImageStorage)

    def __str__(self):
        return f'Camera {self.camera_id}'


class SensorLogs(models.Model):
    sensor_id = models.ForeignKey(SensorCamera, on_delete=models.CASCADE)
    depth = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)
    flood_number = models.IntegerField()

    def __str__(self):
        return f'Sensor {self.sensor_id}'
