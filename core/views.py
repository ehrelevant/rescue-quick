from django.shortcuts import render

from .models import Camera


def index(request):
    camera_list = Camera.objects.all()
    context = {
        'monitors' : [
            {
                'location' : 'Alumni Engineers Centennial Hall, 4F',
                'camera_name' : 'ESP3123',
                'date' : 'April 20, 2025',
                'num_people' : 2,
                'num_pets' : 3,
                'flood_level' : 0.65,
                'max_flood_level' : 1.75,
            }
        ]
        
    }

    return render(request, 'core/index.html.j2', context)
