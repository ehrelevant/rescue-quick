import base64
from django.shortcuts import redirect, render

from .models import SensorCamera, SensorLogs, CameraLogs

from django.http import HttpRequest, HttpResponseNotFound, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from django.core.files.base import ContentFile
from uuid import uuid4
from datetime import datetime

import json


def index(request: HttpRequest):
    # Currently just taking the frst entry (i.e. assume only 1 camera)
    # Should eventually become a list of the first entry of each unique pair_id
    # sensor_data = SensorCamera.objects.order_by('-timestamp').first()
    # print(sensor_data)

    dangerous_sensor_cameras = SensorCamera.objects.filter(monitor_state=SensorCamera.MonitorState.DANGEROUS).all()
    monitors = [
        {
            'location': sensor_camera.location,
            'camera_name': sensor_camera.pair_name,
            'date': sensor_camera.timestamp.strftime(r'%B %d, %Y'),
            'num_people': 1,
            'num_pets': 2,
            'flood_level': sensor_camera.current_depth,
            'max_flood_level': sensor_camera.threshold_depth,
        }
        for sensor_camera in dangerous_sensor_cameras
    ]
    print(monitors)

    context = {
        'monitors': [
            {
                'location': 'Alumni Engineers Centennial Hall, 4F',
                'camera_name': 'ESP3123',
                'date': 'April 20, 2025',
                'num_people': 2,
                'num_pets': 3,
                'flood_level': 0.65,
                'max_flood_level': 1.75,
            },
            *monitors,
        ],
        'operations': [
            {
                'location': 'Alumni Engineers Centennial Hall, 4F',
                'camera_name': 'ESP3123',
                'date': 'April 20, 2025',
                'time_elapsed': '2 min ago',
            }
        ],
        'done': [
            {
                'location': 'Alumni Engineers Centennial Hall, 4F',
                'camera_name': 'ESP3123',
                'date': 'April 20, 2025',
                'marked_safe': '11:00 AM',
                'num_people': 2,
                'num_pets': 3,
                'flood_level': 0.65,
            }
        ],
    }
    return render(request, 'core/index.html.j2', context)

def feed(request: HttpRequest, pair_id: int | None = None):
    if not pair_id:
        sensor_camera = SensorCamera.objects.first()
        
        # Return a 404 error if the table is empty
        if not sensor_camera:
            return HttpResponseNotFound('No cameras found')
        
        # For consistency, redirect to page
        return redirect(f'/feed/{sensor_camera.pair_id}/')

    last_camera_log = CameraLogs.objects.filter(camera_id=pair_id).order_by('-timestamp').first()

    # Returns a 404 error if the queried pair_id does not exist
    if not last_camera_log:
        return HttpResponseNotFound('Camera not found')

    processed_image_url = last_camera_log.processed_image_url 

    sensor_camera = SensorCamera.objects.get(pk=pair_id)    

    # Determines next/previous pair_id
    next_sensor_camera = SensorCamera.objects.filter(pair_id__gt=pair_id).last() or SensorCamera.objects.filter(pair_id__lt=pair_id).first()
    prev_sensor_camera = SensorCamera.objects.filter(pair_id__lt=pair_id).first() or SensorCamera.objects.filter(pair_id__gt=pair_id).last()
    next_pair_id = pair_id
    prev_pair_id = pair_id
    if next_sensor_camera:
        next_pair_id = next_sensor_camera.pair_id
    if prev_sensor_camera:
        prev_pair_id = prev_sensor_camera.pair_id

    # Collates values 
    context = {
        'pair_id': pair_id,
        'location': sensor_camera.location,
        'camera_name': sensor_camera.pair_name,
        'date': sensor_camera.timestamp.strftime(r'%Y/%m/%d'),
        'marked_safe': sensor_camera.state_change_timestamp.strftime(r'%Y/%m/%d %H:%M:%S $p'),
        'num_people': 123,
        'num_pets': 123,
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
        return render(request, 'core/feed/safe.html.j2', context)


# Remove csrf_exempt eventually
@csrf_exempt
@require_POST
def post_sensor_data(request: HttpRequest):
    # print("=== Incoming Request ===")
    # print("Method:", request.method)
    # print("Headers:", dict(request.headers))
    # print("Raw Body:", request.body)
    # print("========================")

    try:
        data = json.loads(request.body)
        print('Parsed JSON:', data)

        sensor_camera, _ = SensorCamera.objects.update_or_create(
            pair_id=data['pair_id'],
            defaults={
                'current_depth': data['current_depth'],
                'flood_number': data['flood_number'],
            },
            create_defaults={
                'current_depth': data['current_depth'],
                'flood_number': data['flood_number'],
                'location': '',
            },
        )

        # Missing threshold condition
        SensorLogs.objects.create(
            sensor_id=sensor_camera,
            depth=sensor_camera.current_depth,
            flood_number=sensor_camera.flood_number,
        )

        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


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
                sensor_cam.current_depth >= sensor_cam.threshold_depth
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
def post_image(request: HttpRequest, pair_id: str):
    try:
        # Get Sensor Camera Pair ID
        sensor_cam: SensorCamera | None = None
        data = json.loads(request.body)
        img_data = data.get('image')

        if not img_data:
            return JsonResponse(
                {'status': 'error', 'message': 'No image uploaded'}, status=400
            )

        # Convert base64 image to actual image
        decoded_img = base64.b64decode(img_data)
        img_name = f'{uuid4()}.jpg'
        img_file = ContentFile(decoded_img, name=img_name)

        # Find appropriate Sensor Camera Pair
        if pair_id.isdigit():
            pair_id_int: int = int(pair_id)
            sensor_cam = SensorCamera.objects.get(pair_id=pair_id_int)
        else:
            return JsonResponse(
                {'status': 'error', 'message': 'Invalid camera ID'}, status=400
            )

        # TODO: Add function for processing images 
        processed_file = img_file

        # Add image to camera logs
        CameraLogs.objects.create(
            camera_id=sensor_cam, flood_number=sensor_cam.flood_number, image=img_file, image_processed=processed_file
        )

        return JsonResponse(
            {'status': 'success', 'message': 'Upload successful', 'filename': img_name}
        )
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


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
