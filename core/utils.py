from django.http import JsonResponse
from .models import SensorCamera, SensorLogs
import typing
from pytz import timezone
from datetime import timedelta


def convert_time(delta: timedelta) -> str:
    s = delta.seconds
    d = delta.days

    if d == 1:
        return '1 day'
    elif d > 1 and d <= 30:
        return f'{d} days'
    elif d == 0 and s <= 1:
        return 'Less than a second'
    elif d == 0 and s < 60:
        return f'{s} seconds'
    elif d == 0 and s < 120:
        return '1 minute'
    elif d == 0 and s < 3600:
        return f'{s // 60} minutes'
    elif d == 0 and s < 7200:
        mins = (s-3600)//60
        mins_text = f"{mins} minutes " if mins > 1 else ""
        return f'1 hour {mins_text}'
    elif d == 0 and s < 86400:
        hours = s//3600
        mins = (s - 3600*hours) // 60
        mins_text = f"{mins} minutes " if mins > 1 else ""
        return f'{hours} hours {mins_text}'
    else:
        return str(delta)


def authenticate_device(view_func):
    def wrapper(request, *args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse({'message': 'Unauthorized'}, status=401)

        token = auth_header.split(' ')[1]
        try:
            request.sensor_cam = SensorCamera.objects.get(token=token)
        except SensorCamera.DoesNotExist:
            return JsonResponse({'message': 'Invalid token'}, status=401)

        return view_func(request, *args, **kwargs)

    return wrapper


def collect_done_operations() -> list[dict[str, typing.Any]]:
    # Get all the sensor cameras available
    sensor_cams = SensorCamera.objects.all()

    # Get their pair_id and flood_number
    current_values = [
        {
            'pair_id': sensor_cam.pair_id,
            'current_flood': sensor_cam.flood_number,
            'location': sensor_cam.location,
            'camera_name': sensor_cam.pair_name,
        }
        for sensor_cam in sensor_cams
    ]

    # List to hold final operations
    operations = []

    for value in current_values:
        for flood_num in range(value['current_flood'] - 1, -1, -1):
            sensor_logs = (
                SensorLogs.objects.filter(
                    sensor_id__pair_id=value['pair_id'], flood_number=flood_num
                )
                .order_by('-timestamp')
                .all()
            )

            if sensor_logs:
                timestamp = sensor_logs.first().timestamp
                day = timestamp.date()
                proper_time = timestamp.astimezone(timezone('Asia/Hong_Kong'))

                delta = sensor_logs.first().timestamp - sensor_logs.last().timestamp
                duration = convert_time(delta)

                operations.append(
                    {
                        'location': value['location'],
                        'camera_name': value['camera_name'],
                        'date': day.strftime(r'%B %d, %Y'),
                        'marked_safe': proper_time.strftime(r'%I:%M %p'),
                        'duration': duration,
                        'flood_level': sensor_logs.order_by('-depth').first().depth
                        if sensor_logs.order_by('-depth').first() is not None
                        else 0,
                        'timestamp': timestamp,
                    }
                )

    sorted_operations = sorted(operations, key=lambda x: x['timestamp'], reverse=True)
    return sorted_operations
