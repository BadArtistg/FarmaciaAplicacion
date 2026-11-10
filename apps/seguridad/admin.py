from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, AuditoriaEvento


@admin.register(Usuario)
class CustomUsuarioAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'rol', 'bloqueado', 'intentos_fallidos', 'dos_factores_activo', 'is_active')
    list_filter = ('rol', 'bloqueado', 'dos_factores_activo', 'is_active')
    fieldsets = UserAdmin.fieldsets + (
        ('Control de Acceso y Práctica INACAP', {
            'fields': ('rol', 'intentos_fallidos', 'bloqueado', 'dos_factores_activo', 'secreto_otp')
        }),
    )
    actions = ['desbloquear_usuarios']

    @admin.action(description='Desbloquear cuentas seleccionadas')
    def desbloquear_usuarios(self, request, queryset):
        for user in queryset:
            user.desbloquear()
        self.message_user(request, f"{queryset.count()} usuario(s) desbloqueado(s) exitosamente.")


@admin.register(AuditoriaEvento)
class AuditoriaEventoAdmin(admin.ModelAdmin):
    list_display = ('fecha_hora', 'usuario_str', 'accion', 'entidad', 'ip')
    list_filter = ('accion', 'entidad', 'fecha_hora')
    search_fields = ('usuario_str', 'accion', 'entidad', 'ip')
    readonly_fields = ('usuario', 'usuario_str', 'accion', 'entidad', 'fecha_hora', 'ip', 'detalle')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
