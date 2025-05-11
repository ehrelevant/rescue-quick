from celery import shared_task
import base64
import numpy as np
from PIL import Image
from io import BytesIO
import cv2
from ultralytics import YOLO
from collections import Counter
from django.core.files.base import ContentFile
from .models import SensorCamera, CameraLogs


@shared_task
def process_image_yolo(pair_id, img_data, img_name):
    decoded_img = base64.b64decode(img_data)
    sensor_cam = SensorCamera.objects.get(pair_id=pair_id)

    pil_image = Image.open(BytesIO(decoded_img)).convert('RGB')
    img_array = np.array(pil_image)

    model = YOLO('yolo11n.pt')
    model_results = model(img_array, classes=[0, 15, 16])
    detections = model_results[0]
    rendered_img = model_results[0].plot()

    rendered_img_bgr = cv2.cvtColor(rendered_img, cv2.COLOR_RGB2BGR)
    _, encoded_img = cv2.imencode('.jpg', rendered_img_bgr)

    img_file = ContentFile(decoded_img, name=img_name)
    img_processed_file = ContentFile(
        encoded_img.tobytes(), name=f'processed_{img_name}.jpg'
    )

    class_ids = detections.boxes.cls.cpu().numpy().astype(int)
    class_counts = Counter(class_ids)

    CameraLogs.objects.create(
        camera_id=sensor_cam,
        flood_number=sensor_cam.flood_number,
        person_count=class_counts.get(0, 0),
        dog_count=class_counts.get(16, 0),
        cat_count=class_counts.get(15, 0),
        image=img_file,
        image_processed=img_processed_file,
    )

    if (
        sum([class_counts.get(0, 0), class_counts.get(16, 0), class_counts.get(15, 0)])
        > 0
        and sensor_cam.monitor_state == SensorCamera.MonitorState.CAUTION
    ):
        sensor_cam.monitor_state = SensorCamera.MonitorState.DANGEROUS
        sensor_cam.save()
    elif (
        sum([class_counts.get(0, 0), class_counts.get(16, 0), class_counts.get(15, 0)])
        == 0
        and sensor_cam.monitor_state == SensorCamera.MonitorState.DANGEROUS
    ):
        sensor_cam.monitor_state = SensorCamera.MonitorState.CAUTION
        sensor_cam.save()

    SensorCamera.objects.filter(pair_id=pair_id).update(
        person_count=class_counts.get(0, 0),
        dog_count=class_counts.get(16, 0),
        cat_count=class_counts.get(15, 0),
    )
