from django.apps import AppConfig
import os
from sahi.utils.ultralytics import download_yolo11n_model

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    # Download the YOLO model once
    def ready(self):
        model_path = os.path.join(os.path.dirname(__file__), '..', 'yolo11n.pt')
        if not os.path.exists(model_path):
            try:
                print("Downloading YOLO model...")
                download_yolo11n_model(model_path)
            except Exception as e:
                print(f"Failed to download YOLO model: {e}")
