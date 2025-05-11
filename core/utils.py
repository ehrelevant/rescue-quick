from django.http import JsonResponse
from .models import SensorCamera

def authenticate_device(view_func):
    def wrapper(request, *args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JsonResponse({'message': 'Unauthorized'}, status=401)

        token = auth_header.split(" ")[1]
        try:
            request.sensor_cam = SensorCamera.objects.get(token=token)
        except SensorCamera.DoesNotExist:
            return JsonResponse({'message': 'Invalid token'}, status=401)

        return view_func(request, *args, **kwargs)
    return wrapper