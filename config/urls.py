from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', lambda request: redirect('inventario:dashboard' if request.user.is_authenticated else 'seguridad:login')),
    path('seguridad/', include('apps.seguridad.urls', namespace='seguridad')),
    path('inventario/', include('apps.inventario.urls', namespace='inventario')),
    path('recetas/', include('apps.recetas.urls', namespace='recetas')),
    path('dispensacion/', include('apps.dispensacion.urls', namespace='dispensacion')),
    path('caja/', include('apps.caja.urls', namespace='caja')),
]
