from django.urls import path
from django.http import HttpResponse

app_name = 'recetas'

def placeholder_view(request):
    return HttpResponse("Módulo de Recetas preparado para el Sprint 2.")

urlpatterns = [
    path('', placeholder_view, name='index'),
]
