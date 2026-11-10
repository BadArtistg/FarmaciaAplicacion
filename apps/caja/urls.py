from django.urls import path
from django.http import HttpResponse

app_name = 'caja'

def placeholder_view(request):
    return HttpResponse("Módulo de Caja y Cobro Simulado preparado para el Sprint 3.")

urlpatterns = [
    path('', placeholder_view, name='index'),
]
