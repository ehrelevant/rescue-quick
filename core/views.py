import base64
from django.db.models import QuerySet
from django.shortcuts import redirect, render
from django.utils import timezone

from .models import SensorCamera, SensorLogs, CameraLogs

from django.http import HttpRequest, HttpResponseNotFound, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from django.core.files.base import ContentFile
from uuid import uuid4

import json
from collections import Counter

from ultralytics import YOLO
import cv2
from PIL import Image
from io import BytesIO
import numpy as np
import typing
from .tasks import process_image_yolo


def check_health():
    seconds_threshold = 5  # 5 Seconds
    for sensor_camera in SensorCamera.objects.all():
        sensor_time = timezone.now() - sensor_camera.last_sensor_report
        camera_time = timezone.now() - sensor_camera.last_camera_report
        if (
            sensor_time.seconds > seconds_threshold
            and camera_time.seconds > seconds_threshold
        ):
            sensor_camera.monitor_state = SensorCamera.MonitorState.UNRESPONSIVE_BOTH
        elif sensor_time.seconds > seconds_threshold:
            sensor_camera.monitor_state = SensorCamera.MonitorState.UNRESPONSIVE_SENSOR
        elif camera_time.seconds > seconds_threshold:
            sensor_camera.monitor_state = SensorCamera.MonitorState.UNRESPONSIVE_CAMERA
        sensor_camera.save()


def index(request: HttpRequest):
    check_health()

    dangerous_sensor_cameras = SensorCamera.objects.filter(
        monitor_state=SensorCamera.MonitorState.DANGEROUS
    ).all()
    caution_sensor_cameras = SensorCamera.objects.filter(
        monitor_state=SensorCamera.MonitorState.CAUTION
    ).all()
    safe_sensor_cameras = SensorCamera.objects.filter(
        monitor_state=SensorCamera.MonitorState.SAFE
    ).all()
    unresponsive_sensor_cameras = SensorCamera.objects.filter(
        monitor_state=SensorCamera.MonitorState.UNRESPONSIVE_BOTH
    ).all()
    unresponsive_sensors = SensorCamera.objects.filter(
        monitor_state=SensorCamera.MonitorState.UNRESPONSIVE_SENSOR
    ).all()
    unresponsive_cameras = SensorCamera.objects.filter(
        monitor_state=SensorCamera.MonitorState.UNRESPONSIVE_CAMERA
    ).all()

    def collect_monitors(
        sensor_cameras: QuerySet[SensorCamera, SensorCamera],
    ) -> list[dict[str, typing.Any]]:
        return [
            {
                'location': sensor_camera.location,
                'camera_name': sensor_camera.pair_name,
                'date': sensor_camera.timestamp.strftime(r'%B %d, %Y'),
                'num_people': sensor_camera.person_count,
                'num_cats': sensor_camera.cat_count,
                'num_dogs': sensor_camera.dog_count,
                'flood_level': sensor_camera.current_depth,
                'max_flood_level': sensor_camera.threshold_depth,
            }
            for sensor_camera in sensor_cameras
        ]

    monitors: dict[str, typing.Any] = {
        'danger': collect_monitors(dangerous_sensor_cameras),
        'caution': collect_monitors(caution_sensor_cameras),
        'safe': collect_monitors(safe_sensor_cameras),
        'unresponsive_both': collect_monitors(unresponsive_sensor_cameras),
        'unresponsive_sensor': collect_monitors(unresponsive_sensors),
        'unresponsive_camera': collect_monitors(unresponsive_cameras),
    }

    operations: list[dict[str, typing.Any]] = [
        {
            'location': sensor_camera.location,
            'camera_name': sensor_camera.pair_name,
            'date': sensor_camera.timestamp.strftime(r'%B %d, %Y'),
            'time_elapsed': sensor_camera.elapsed_time,
            'is_long_time': sensor_camera.is_long_time,
            'is_deployed': False,
        }
        for sensor_camera in dangerous_sensor_cameras.order_by(
            'state_change_timestamp'
        ).all()
    ]

    context: dict[str, typing.Any] = {
        'monitors': monitors,
        'operations': [
            {
                'location': 'Location X',
                'camera_name': 'ESP3123 Test 1',
                'date': 'May 2, 2025',
                'time_elapsed': '17 minutes ago',
                'is_long_time': False,
                'is_deployed': False,
            },
            {
                'location': 'Location Y',
                'camera_name': 'ESP3123 Test 2',
                'date': 'May 2, 2025',
                'time_elapsed': '2 hours ago',
                'is_long_time': True,
                'is_deployed': False,
            },
            {
                'location': 'Location Z',
                'camera_name': 'ESP3123 Test 3',
                'date': 'May 2, 2025',
                'time_elapsed': '2 hours ago',
                'is_long_time': True,
                'is_deployed': True,
            },
            *operations,
        ],
        'done': [
            {
                'location': 'Alumni Engineers Centennial Hall, 4F',
                'camera_name': 'ESP3123',
                'date': 'April 20, 2025',
                'marked_safe': '11:00 AM',
                'num_people': 2,
                'num_cats': 1,
                'num_dogs': 2,
                'flood_level': 0.65,
            }
        ],
        'counts': {
            'danger': dangerous_sensor_cameras.count(),
            'caution': caution_sensor_cameras.count(),
            'safe': safe_sensor_cameras.count(),
            'unresponsive': unresponsive_sensor_cameras.count()
            + unresponsive_sensors.count()
            + unresponsive_cameras.count(),
        },
    }
    return render(request, 'core/index.html.j2', context)


def feed(request: HttpRequest, pair_id: int | None = None):
    sensor_camera: SensorCamera | None = None

    if not pair_id:
        sensor_camera = SensorCamera.objects.first()

        print('TEST:', sensor_camera)

        # Return a 404 error if the table is empty
        if not sensor_camera:
            return HttpResponseNotFound('No cameras found')

        # For consistency, redirect to page
        return redirect(f'/feed/{sensor_camera.pair_id}/')

    last_camera_log = (
        CameraLogs.objects.filter(
            camera_id=pair_id,
            # flood_number=sensor_camera.flood_number
        )
        .order_by('-timestamp')
        .first()
    )

    # Returns a 404 error if the queried pair_id does not exist
    if not last_camera_log:
        return HttpResponseNotFound('Camera not found')

    processed_image_url = last_camera_log.processed_image_url
    # processed_image_url = 'https://www.rappler.com/tachyon/2025/05/ahtisa-manalo-miss-univere-ph-may-3-2025.jpg'

    sensor_camera = SensorCamera.objects.get(pk=pair_id)

    # Determines next/previous pair_id
    next_sensor_camera = (
        SensorCamera.objects.filter(pair_id__gt=pair_id).first()
        or SensorCamera.objects.filter(pair_id__lt=pair_id).first()
    )
    prev_sensor_camera = (
        SensorCamera.objects.filter(pair_id__lt=pair_id).last()
        or SensorCamera.objects.filter(pair_id__gt=pair_id).last()
    )
    next_pair_id = pair_id
    prev_pair_id = pair_id
    if next_sensor_camera:
        next_pair_id = next_sensor_camera.pair_id
    if prev_sensor_camera:
        prev_pair_id = prev_sensor_camera.pair_id

    # Collates values
    context: dict[str, typing.Any] = {
        'pair_id': pair_id,
        'location': sensor_camera.location,
        'camera_name': sensor_camera.pair_name,
        'date': sensor_camera.timestamp.strftime(r'%Y/%m/%d'),
        'marked_safe': sensor_camera.state_change_timestamp.strftime(
            r'%Y/%m/%d %H:%M:%S %p'
        ),
        'num_people': sensor_camera.person_count,
        'num_dogs': sensor_camera.dog_count,
        'num_cats': sensor_camera.cat_count,
        'flood_level': sensor_camera.current_depth,
        'processed_image': processed_image_url,
        # For testing of pagination lang
        'prev': prev_pair_id,
        'next': next_pair_id,
    }

    if sensor_camera.monitor_state == SensorCamera.MonitorState.DANGEROUS:
        return render(request, 'core/feed/danger.html.j2', context)
    elif sensor_camera.monitor_state == SensorCamera.MonitorState.CAUTION:
        return render(request, 'core/feed/caution.html.j2', context)
    else:
        return render(request, 'core/feed/danger.html.j2', context)


# =============== Sensor Views ===============
@csrf_exempt
@require_POST
def post_sensor_data(request: HttpRequest, pair_id: int):
    try:
        data = json.loads(request.body)

        sensor_camera, _ = SensorCamera.objects.update_or_create(
            pair_id=pair_id,
            defaults={
                'current_depth': max(data['current_depth'], 0),
                'last_sensor_report': timezone.now(),
                'is_wet': data['is_wet'],
            },
            create_defaults={
                'pair_name': f'Camera {pair_id}',
                'current_depth': max(data['current_depth'], 0),
                'location': f'Location {pair_id}',
                'monitor_state': SensorCamera.MonitorState.SAFE,
                'is_wet': data['is_wet'],
            },
        )
        # Update Monitor State
        if (
            sensor_camera.current_depth > sensor_camera.threshold_depth
            and sensor_camera.is_wet
            and sensor_camera.monitor_state == SensorCamera.MonitorState.SAFE
        ):
            SensorCamera.objects.filter(pair_id=pair_id).update(
                monitor_state=SensorCamera.MonitorState.CAUTION
            )
        elif (
            sensor_camera.current_depth <= sensor_camera.threshold_depth
            or not sensor_camera.is_wet
            or sensor_camera.monitor_state
            == SensorCamera.MonitorState.UNRESPONSIVE_CAMERA
            or sensor_camera.monitor_state
            == SensorCamera.MonitorState.UNRESPONSIVE_BOTH
            or sensor_camera.monitor_state
            == SensorCamera.MonitorState.UNRESPONSIVE_SENSOR
        ):
            SensorCamera.objects.filter(pair_id=pair_id).update(
                monitor_state=SensorCamera.MonitorState.SAFE
            )

        # Log Sensor Data if CAUTION or DANGEROUS
        if (
            sensor_camera.monitor_state == SensorCamera.MonitorState.CAUTION
            or sensor_camera.monitor_state == SensorCamera.MonitorState.DANGEROUS
        ):
            SensorLogs.objects.create(
                sensor_id=sensor_camera,
                depth=sensor_camera.current_depth,
                flood_number=sensor_camera.flood_number,
            )

        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


# ============================================


# =============== Camera Views ===============
@csrf_exempt
@require_GET
def get_flood_status(request: HttpRequest):
    # Get the pair id from the request url
    pair_id: str | None = request.GET.get('pair_id')
    sensor_cam: SensorCamera | None = None

    if pair_id is not None and pair_id.isdigit():
        pair_id_int: int = int(pair_id)

        try:
            # Find the appropriate Sensor Camera Pair
            sensor_cam = SensorCamera.objects.get(pair_id=pair_id_int)

            # Get the latest indicator
            indicator: str = str(
                sensor_cam.current_depth > sensor_cam.threshold_depth
            ).lower()

            # Return as a JSON Response
            return JsonResponse({'status': 'success', 'indicator': indicator})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    else:
        return JsonResponse(
            {'status': 'error', 'message': 'Invalid pair id'}, status=400
        )


@csrf_exempt
@require_POST
def post_image(request: HttpRequest, pair_id: int):
    try:
        # Get Sensor Camera Pair ID
        data = json.loads(request.body)
        img_data = data.get('image')

        if not img_data:
            return JsonResponse(
                {'status': 'error', 'message': 'No image uploaded'}, status=400
            )

        img_name = f'{uuid4()}.jpg'

        # Use celery task to asynchronously process the image
        process_image_yolo.delay(pair_id, img_data, img_name)

        return JsonResponse(
            {'status': 'success', 'message': 'Upload successful', 'filename': img_name}
        )
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@csrf_exempt
@require_POST
def post_cam_health(request: HttpRequest, pair_id: int):
    try:
        # Get Sensor Camera Pair ID
        data = json.loads(request.body)
        state: str = data.get('state', '')

        # Update the health report
        if state == 'alive':
            SensorCamera.objects.filter(pair_id=pair_id).update(
                last_camera_report=timezone.now()
            )

            return JsonResponse(
                {'status': 'success', 'message': 'Camera is alive received'}
            )
        else:
            return JsonResponse(
                {'status': 'error', 'message': 'Camera health update failed'},
                status=400,
            )
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


# ============================================


@csrf_exempt
@require_GET
def get_available_pair_id(_):
    """
    Returns a pair ID that is currently unreserved.
    Specifically, this returns the largest pair ID plus 1.
    """
    try:
        last_sensor_cam: SensorCamera | None = SensorCamera.objects.order_by(
            '-pair_id'
        ).first()
        available_id = last_sensor_cam.pair_id + 1 if last_sensor_cam else 1

        return JsonResponse({'status': 'success', 'pair_id': available_id})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@csrf_exempt
@require_POST
def post_reserve_pair_id(request: HttpRequest):
    """
    Reserves the requested pair ID in the database.
    This allows a pair ID to be held by a sensor without sending sensor data.
    """
    try:
        data = json.loads(request.body)
        target_pair_id = data['pair_id']
        if SensorCamera.objects.filter(pair_id=target_pair_id).exists():
            # Errors if requested pair ID is already reserved for a different resource
            return JsonResponse(
                {'status': 'error', 'message': 'Pair ID has already been assigned.'},
                status=400,
            )

        SensorCamera.objects.create(
            pair_id=target_pair_id, pair_name=f'Camera {target_pair_id}'
        )

        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
