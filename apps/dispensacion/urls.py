from django.urls import path
from django.http import HttpResponse

app_name = 'dispensacion'

def placeholder_view(request):
    return HttpResponse("Módulo de Dispensación preparado para los Sprints 2 y 3.")

urlpatterns = [
    path('', placeholder_view, name='index'),
]
