from django.urls import path
from . import views

app_name = 'seguridad'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('login/2fa/', views.two_factor_verify_view, name='two_factor'),
    path('logout/', views.logout_view, name='logout'),
    path('usuarios/', views.usuario_list_view, name='usuario_list'),
    path('usuarios/nuevo/', views.usuario_create_view, name='usuario_create'),
    path('usuarios/<int:pk>/editar/', views.usuario_update_view, name='usuario_update'),
    path('usuarios/<int:pk>/desbloquear/', views.usuario_desbloquear_view, name='usuario_desbloquear'),
    path('auditoria/', views.auditoria_list_view, name='auditoria'),
]
