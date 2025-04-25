from django.db import models


class SensorCamera(models.Model):
    pair_id = models.IntegerField(primary_key=True)
    current_depth = models.FloatField()
    location = models.TextField()
    flood_number = models.IntegerField()
    timestamp = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.location}: Time {self.timestamp} - Depth {self.current_depth}'


class CameraLogs(models.Model):
    # Missing Image Data
    camera_id = models.ForeignKey(SensorCamera, on_delete=models.CASCADE)
    flood_number = models.IntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Camera {self.camera_id}'


class SensorLogs(models.Model):
    sensor_id = models.ForeignKey(SensorCamera, on_delete=models.CASCADE)
    depth = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)
    flood_number = models.IntegerField()

    def __str__(self):
        return f'Sensor {self.sensor_id}'
