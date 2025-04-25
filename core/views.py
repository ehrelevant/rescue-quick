from django.shortcuts import render

from .models import SensorCamera

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

import json


def index(request):
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
        'operations' : [
            {
                'location' : 'Alumni Engineers Centennial Hall, 4F',
                'camera_name' : 'ESP3123',
                'date' : 'April 20, 2025',
                'time_elapsed' : '2 min ago',
            }
        ],
        'done' : [
            {
                'location' : 'Alumni Engineers Centennial Hall, 4F',
                'camera_name' : 'ESP3123',
                'date' : 'April 20, 2025',
                'marked_safe' : '11:00 AM',
                'num_people' : 2,
                'num_pets' : 3,
                'flood_level' : 0.65,
            }
        ],
        'sensor_data': sensor_data,
    }
    return render(request, 'core/index.html.j2', context)


# Remove csrf_exempt eventually
@csrf_exempt
@require_POST
def sensor_data(request):
    # print("=== Incoming Request ===")
    # print("Method:", request.method)
    # print("Headers:", dict(request.headers))
    # print("Raw Body:", request.body)
    # print("========================")

    try:
        data = json.loads(request.body)
        print('Parsed JSON:', data)
        SensorCamera.objects.update_or_create(
            pair_id=data['pair_id'],
            defaults={
                'current_depth': data['current_depth'],
                'location': data['location'],
                'flood_number': data['flood_number'],
            },
        )
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
