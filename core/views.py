import base64
from django.shortcuts import render

from .models import SensorCamera, SensorLogs, CameraLogs

from django.http import HttpRequest
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from django.core.files.base import ContentFile
from uuid import uuid4

import json


def index(request: HttpRequest):
    # Currently just taking the frst entry (i.e. assume only 1 camera)
    # Should eventually become a list of the first entry of each unique pair_id
    # sensor_data = SensorCamera.objects.order_by('-timestamp').first()
    # print(sensor_data)
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
            }
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
        # 'sensor_data': sensor_data,
    }
    return render(request, 'core/index.html.j2', context)


def feed(request: HttpRequest, monitor_id: int):
    context = {
        'monitor_id': monitor_id,
        'location': 'Alumni Engineers Centennial Hall, 4F',
        'camera_name': 'ESP3123',
        'date': 'April 20, 2025',
        'marked_safe': '11:00 AM',
        'num_people': 2,
        'num_pets': 3,
        'flood_level': 0.65,
        # For testing of pagination lang
        'prev': (monitor_id - 1) % 3,
        'next': ((monitor_id % 3) + 1) % 3,
    }

    if monitor_id == 1:
        return render(request, 'core/feed/danger.html.j2', context)
    elif monitor_id == 2:
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
            indicator: str = str(sensor_cam.current_depth >= sensor_cam.threshold_depth).lower()

            # Return as a JSON Response
            return JsonResponse({'status': 'success', 'indicator': indicator})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid pair id'}, status=400)


@csrf_exempt
@require_POST
def post_image(request: HttpRequest, pair_id: str):
    try:
        # Get Sensor Camera Pair ID
        sensor_cam: SensorCamera | None = None
        data = json.loads(request.body)
        img_data = data.get('image')
        
        if not img_data:
            return JsonResponse({'status': 'error', "message": "No image uploaded"}, status=400)
        
        # Convert base64 image to actual image
        decoded_img = base64.b64decode(img_data)
        img_name = f'{uuid4()}.jpg'
        img_file = ContentFile(decoded_img, name=img_name)

        # Find appropriate Sensor Camera Pair
        if pair_id.isdigit():
            pair_id_int: int = int(pair_id)
            sensor_cam = SensorCamera.objects.get(pair_id=pair_id_int)
        else:
            return JsonResponse({'status': 'error', 'message': 'Invalid camera ID'}, status=400)

        # Add image to camera logs
        CameraLogs.objects.create(
            camera_id=sensor_cam,
            flood_number=sensor_cam.flood_number,
            image=img_file
        )

        return JsonResponse({"status": "success", "message": "Upload successful", "filename": img_name})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)