from django.db import models

class Camera(models.Model):
    name = models.CharField(max_length=200)
    location = models.TextField()

    def __str__(self):
        return f'Camera "{self.name}" | Location: {self.location}'