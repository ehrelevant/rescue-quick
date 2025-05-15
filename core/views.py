import base64
from django.db.models import QuerySet
from django.shortcuts import redirect, render
from django.utils import timezone

from .models import SensorCamera, SensorLogs, CameraLogs, RescuerContacts, elapsed_time
from .utils import collect_done_operations

from django.http import (
    HttpRequest,
    HttpResponseNotFound,
    JsonResponse,
    HttpResponseRedirect,
)
from django.views.decorators.csrf import csrf_exempt, csrf_protect
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
import secrets
from .utils import authenticate_device

import resend
from django.template.loader import render_to_string

from .forms import MonitorForm


@csrf_exempt
@require_POST
def signal_rescue(request: HttpRequest):
    try:
        pair_id = request.POST.get('pair_id', '')
        camera_name = request.POST.get('camera_name', 'unknown')
        time_elapsed = request.POST.get('time_elapsed', 'unknown')
        location = request.POST.get('location', 'unknown')
        site = request.POST.get('site', '/')

        rescuers = RescuerContacts.objects.filter(devices__pair_id=int(pair_id)).all()
        emails = [rescuer.email_addr for rescuer in rescuers]
        context = {
            'camera_name': camera_name,
            'time_elapsed': time_elapsed,
            'location': location,
        }

        message = render_to_string('core/emails/new_flood_alert.html', context)
        
        resend.Emails.send(
            {
                'from': 'RescueQuick <send@rescue-quick.ehrencastillo.tech>',
                'to': emails,
                'subject': 'Hey! Listen!',
                'html': message,
            }
        )
        
        return HttpResponseRedirect(site)
    except Exception as e:
        print(e)
        print(JsonResponse({'status': 'error', 'message': str(e)}, status=500))
        return HttpResponseRedirect('/')


def check_health():
    seconds_threshold = 5  # 5 Seconds
    for sensor_camera in SensorCamera.objects.all():
        if (not sensor_camera.last_sensor_report):
            sensor_time = timezone.now() - timezone.make_aware(timezone.datetime(1999, 1, 1))
        else:
            sensor_time = timezone.now() - sensor_camera.last_sensor_report
        if (not sensor_camera.last_camera_report):
            camera_time = timezone.now() - timezone.make_aware(timezone.datetime(1999, 1, 1))
        else:
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
        sensor_cameras: QuerySet[SensorCamera],
    ) -> list[dict[str, typing.Any]]:
        return [
            {
                'pair_id': sensor_camera.pair_id,
                'location': sensor_camera.location,
                'camera_name': sensor_camera.pair_name,
                'date': sensor_camera.timestamp.strftime(r'%B %d, %Y'),
                'num_people': sensor_camera.person_count,
                'num_cats': sensor_camera.cat_count,
                'num_dogs': sensor_camera.dog_count,
                'flood_level': sensor_camera.current_depth,
                'max_flood_level': sensor_camera.threshold_depth,
                'sensor_health_time': elapsed_time(sensor_camera.last_sensor_report),
                'camera_health_time': elapsed_time(sensor_camera.last_camera_report),
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
            'pair_id': sensor_camera.pair_id,
            'location': sensor_camera.location,
            'camera_name': sensor_camera.pair_name,
            'date': sensor_camera.timestamp.strftime(r'%B %d, %Y'),
            'time_elapsed': elapsed_time(sensor_camera.state_change_timestamp),
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
            *operations,
        ],
        'done': [*collect_done_operations()],
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
    sensor_camera: SensorCamera | None = SensorCamera.objects.filter(pair_id=pair_id).first()

    if not pair_id:
        sensor_camera = SensorCamera.objects.first()

        # Return a 404 error if the table is empty
        if not sensor_camera:
            return HttpResponseNotFound('No cameras found')

        # For consistency, redirect to page
        return redirect(f'/feed/{sensor_camera.pair_id}/')

    if not sensor_camera:
        return HttpResponseNotFound('Camera not found')


    last_camera_log = (
        CameraLogs.objects.filter(
            camera_id=pair_id,
            # flood_number=sensor_camera.flood_number
        )
        .order_by('-timestamp')
        .first()
    )

    if not last_camera_log:
        processed_image_url = ""
    else:
        processed_image_url = last_camera_log.processed_image_url



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
        # For pagination
        'prev': prev_pair_id,
        'next': next_pair_id,
    }

    if sensor_camera.monitor_state == SensorCamera.MonitorState.DANGEROUS:
        return render(request, 'core/feed/danger.html.j2', context)
    elif sensor_camera.monitor_state == SensorCamera.MonitorState.CAUTION:
        return render(request, 'core/feed/caution.html.j2', context)
    else:
        return render(request, 'core/feed/danger.html.j2', context)


def list_monitors(request: HttpRequest):
    # Collect and Display all the Monitors
    def collect_monitors(
        sensor_cameras: QuerySet[SensorCamera],
    ) -> list[dict[str, typing.Any]]:
        return [
            {
                'pair_id': sensor_camera.pair_id,
                'location': sensor_camera.location,
                'pair_name': sensor_camera.pair_name,
            }
            for sensor_camera in sensor_cameras
        ]

    monitors: typing.Any = collect_monitors(SensorCamera.objects.all())

    context = {'monitors': monitors}

    return render(request, 'core/config/main.html.j2', context)

@csrf_protect
def configure_monitor(request: HttpRequest, pair_id: int):
    # Check if Monitor Exists
    monitor: SensorCamera | None = SensorCamera.objects.filter(pair_id=pair_id).first()
    
                
    if (not monitor):
        return HttpResponseNotFound('Monitor not found')
    
    current_emails = RescuerContacts.objects.filter(
        devices=SensorCamera.objects.get(pair_id=monitor.pair_id)
    ).values_list('email_addr', flat=True)

    string_current_emails = ",".join(current_emails)

    form = MonitorForm(
        request.POST or None, 
        initial={
            "pair_name":monitor.pair_name,
            "threshold_depth":monitor.threshold_depth,
            "pair_id":monitor.pair_id,
            "token":monitor.token,
            "location":monitor.location,
            "emails":string_current_emails
        }
    )

    if request.method == 'POST':
        if "delete-monitor" in request.POST:
            # Delete Monitor from Database
            SensorCamera.objects.filter(pair_id=pair_id).delete()
            return redirect('/configure/')
        elif form.is_valid():
            # Update the Table Entry
            SensorCamera.objects.filter(pair_id=pair_id).update(
                pair_name=form.cleaned_data["pair_name"],
                threshold_depth=form.cleaned_data["threshold_depth"],
                location=form.cleaned_data["location"]
            )
            new_emails = form.cleaned_data["emails"].split(",")
            remove_emails = [item for item in current_emails if item not in new_emails]
            add_emails = [item for item in new_emails if item not in current_emails]

            for email in remove_emails:
                rescuer_contact = RescuerContacts.objects.filter(email_addr=email).first()
                rescuer_contact.devices.remove(SensorCamera.objects.get(pair_id=monitor.pair_id))

                if rescuer_contact.devices.count() == 0:
                    rescuer_contact.delete()

            for email in add_emails:
                rescuer_contact = RescuerContacts.objects.filter(email_addr=email).first()
                if not rescuer_contact: 
                    RescuerContacts.objects.create(email_addr=email)

                rescuer_contact = RescuerContacts.objects.filter(email_addr=email).first()
                rescuer_contact.devices.add(SensorCamera.objects.get(pair_id=monitor.pair_id))    

            # return redirect('/configure/')

    context = {
        'pair_id': pair_id,
        'form' : form,
    }

    return render(request, 'core/config/configure.html.j2', context)

@csrf_exempt
def new_monitor(request: HttpRequest):
    form = MonitorForm(
        request.POST or None,
        initial={
            "pair_name":"",
            "threshold_depth":"",
            "pair_id":"",
            "token":"",
            "location":"",
            "emails":""
        }
    )

    if request.method == 'POST':
        print(form.is_valid())
        if form.is_valid():
            pair_id, token = add_new_monitor(form.cleaned_data["pair_name"], form.cleaned_data["location"], form.cleaned_data["threshold_depth"])
            form.cleaned_data["pair_id"] = pair_id
            form.cleaned_data["token"] = token
            
            for email in form.cleaned_data["emails"].split(","):
                rescuer_contact = RescuerContacts.objects.filter(email_addr=email).first()
                if not rescuer_contact: 
                    RescuerContacts.objects.create(email_addr=email)

                rescuer_contact = RescuerContacts.objects.filter(email_addr=email).first()
                rescuer_contact.devices.add(SensorCamera.objects.get(pair_id=form.cleaned_data["pair_id"]))      

    context = {
        'form' : form,
    }

    return render(request, 'core/config/new.html.j2', context)


# =============== Sensor Views ===============
@csrf_exempt
@require_POST
@authenticate_device
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
@authenticate_device
def get_flood_status(request: HttpRequest):
    # Get the pair id from the request url
    pair_id: str | None = request.GET.get('pair_id')
    sensor_cam: SensorCamera | None = None

    if pair_id is not None and pair_id.isdigit():
        pair_id_int: int = int(pair_id)

        try:
            # Get Sensor Camera based on token
            sensor_cam = request.sensor_cam

            # Extra check
            if sensor_cam.pair_id != pair_id_int:
                return JsonResponse(
                    {
                        'status': 'error',
                        'message': 'Camera id does not match auth token',
                    },
                    status=400,
                )

            # Get the latest indicator
            indicator: str = str(
                sensor_cam.current_depth >= sensor_cam.threshold_depth
                and sensor_cam.is_wet
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
@authenticate_device
def post_image(request: HttpRequest, pair_id: int):
    try:
        # Get Sensor Camera Pair ID
        sensor_cam: SensorCamera | None = None
        data = json.loads(request.body)
        img_data = data.get('image')

        if not img_data:
            return JsonResponse(
                {'status': 'error', 'message': 'No image uploaded'}, status=400
            )

        # Get Sensor Camera based on token
        sensor_cam = request.sensor_cam

        # Extra check
        if sensor_cam.pair_id != pair_id:
            return JsonResponse(
                {'status': 'error', 'message': 'Camera id does not match auth token'},
                status=400,
            )

        # Convert base64 image to actual image
        decoded_img = base64.b64decode(img_data)
        img_name = f'{uuid4()}.jpg'
        img_file = ContentFile(decoded_img, name=img_name)

        # Convert to a format YOLO can use
        pil_image = Image.open(BytesIO(decoded_img)).convert('RGB')
        img_array = np.array(pil_image)

        # Choose and apply model
        model = YOLO('yolo11n.pt')
        model_results = model(img_array, classes=[0, 15, 16])
        detections = model_results[0]
        rendered_img = model_results[0].plot()

        # Convert to BGR for OpenCV encoding
        rendered_img_bgr = cv2.cvtColor(rendered_img, cv2.COLOR_RGB2BGR)

        # Encode image
        _, encoded_img = cv2.imencode('.jpg', rendered_img_bgr)
        img_processed_file = ContentFile(
            encoded_img.tobytes(), name=f'processed_{img_name}'
        )

        # Get class IDs from detections
        class_ids = detections.boxes.cls.cpu().numpy().astype(int)

        # Count each class
        class_counts = Counter(class_ids)
        print('counting ppl', class_counts.get(0, 0))

        # Add image to camera logs
        CameraLogs.objects.create(
            camera_id=sensor_cam,
            flood_number=sensor_cam.flood_number,
            person_count=class_counts.get(0, 0),
            dog_count=class_counts.get(16, 0),
            cat_count=class_counts.get(15, 0),
            image=img_file,
            image_processed=img_processed_file,
        )

        # Update Monitor State
        if (
            sum(
                [
                    class_counts.get(0, 0),
                    class_counts.get(16, 0),
                    class_counts.get(15, 0),
                ]
            )
            > 0
            and sensor_cam.monitor_state == SensorCamera.MonitorState.CAUTION
        ):
            SensorCamera.objects.filter(pair_id=pair_id).update(
                monitor_state=SensorCamera.MonitorState.DANGEROUS
            )
        elif (
            sum(
                [
                    class_counts.get(0, 0),
                    class_counts.get(16, 0),
                    class_counts.get(15, 0),
                ]
            )
            == 0
            and sensor_cam.monitor_state == SensorCamera.MonitorState.DANGEROUS
        ):
            SensorCamera.objects.filter(pair_id=pair_id).update(
                monitor_state=SensorCamera.MonitorState.CAUTION
            )

        # Update CameraSensor with the number of victims
        SensorCamera.objects.filter(pair_id=pair_id).update(
            person_count=class_counts.get(0, 0),
            dog_count=class_counts.get(16, 0),
            cat_count=class_counts.get(15, 0),
        )

        return JsonResponse(
            {'status': 'success', 'message': 'Upload successful', 'filename': img_name}
        )
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@csrf_exempt
@require_POST
@authenticate_device
def post_cam_health(request: HttpRequest, pair_id: int):
    try:
        # Get Sensor Camera based on token
        sensor_cam = request.sensor_cam

        # Extra check
        if sensor_cam.pair_id != pair_id:
            return JsonResponse(
                {'status': 'error', 'message': 'Camera id does not match auth token'},
                status=400,
            )

        # Retrieve data from request
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

def add_new_monitor(input_pair_name, input_location, input_threshold_depth):
    # Generate New Pair ID
    last_sensor_camera: SensorCamera | None = SensorCamera.objects.order_by('-pair_id').first()
    generated_pair_id = last_sensor_camera.pair_id + 1 if last_sensor_camera else 1

    # Generate Token
    generated_token = secrets.token_hex(32)
    while (SensorCamera.objects.filter(token=generated_token).exists()):
        generated_token = secrets.token_hex(32)

    # Create Table Entry
    SensorCamera.objects.create(
            pair_id=generated_pair_id,
            token=generated_token,
            pair_name=input_pair_name,
            location=input_location,
            threshold_depth=input_threshold_depth     
        )
    
    return generated_pair_id, generated_token
