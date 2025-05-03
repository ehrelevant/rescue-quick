from sahi import AutoDetectionModel
from threading import Lock
import os

_model = None
_model_lock = Lock()

def get_detection_model():
    """Function that loads the function. Ensures that it only loads the model once"""
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:  # Double-checked locking
                model_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'yolo11n.pt'))
                _model = AutoDetectionModel.from_pretrained(
                    model_type="ultralytics",
                    model_path=model_path,
                    confidence_threshold=0.3,
                    device="cpu"  # or 'cuda:0'
                )
    return _model