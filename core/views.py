from django.shortcuts import render

from .models import Camera

def index(request):
    camera_list = Camera.objects.all()
    context = {'camera_list': camera_list}

    return render(request, 'core/index.html', context)
