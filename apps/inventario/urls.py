from django.urls import path
from . import views

app_name = 'inventario'

urlpatterns = [
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('productos/', views.producto_list_view, name='producto_list'),
    path('productos/nuevo/', views.producto_create_view, name='producto_create'),
    path('productos/<int:pk>/editar/', views.producto_update_view, name='producto_update'),
    path('lotes/nuevo/', views.lote_create_view, name='lote_create'),
    path('alertas/', views.alertas_list_view, name='alertas'),
]
