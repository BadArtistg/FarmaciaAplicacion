from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone

from apps.seguridad.models import RolUsuario
from apps.seguridad.decorators import requiere_roles
from apps.seguridad.services import registrar_auditoria

from .models import Producto, Lote
from .forms import ProductoForm, LoteForm
from .services import obtener_metricas_dashboard, obtener_alertas_inventario


@requiere_roles(RolUsuario.ESTUDIANTE, RolUsuario.DOCENTE, RolUsuario.QUIMICO, RolUsuario.ADMIN)
def dashboard_view(request):
    """
    Panel principal de la plataforma de farmacia mixta.
    Muestra métricas del inventario y alertas urgentes para la toma de decisiones asistencial.
    """
    metricas = obtener_metricas_dashboard()
    alertas = obtener_alertas_inventario()
    return render(request, 'inventario/dashboard.html', {
        'metricas': metricas,
        'alertas': alertas,
    })


@requiere_roles(RolUsuario.ESTUDIANTE, RolUsuario.DOCENTE, RolUsuario.QUIMICO, RolUsuario.ADMIN)
def producto_list_view(request):
    """
    Catálogo de inventario con orden FEFO (CU-03).
    Muestra los productos con sus lotes ordenados por vencimiento más próximo
    e identifica claramente cuál lote "Sale primero".
    """
    query = request.GET.get('q', '').strip()
    filtro_controlado = request.GET.get('controlado', '').strip()

    productos = Producto.objects.all().prefetch_related('lotes')

    if query:
        productos = productos.filter(
            Q(nombre__icontains=query) |
            Q(codigo__icontains=query) |
            Q(forma_farmaceutica__icontains=query)
        )

    if filtro_controlado == '1':
        productos = productos.filter(es_controlado=True)
    elif filtro_controlado == '0':
        productos = productos.filter(es_controlado=False)

    return render(request, 'inventario/producto_list.html', {
        'productos': productos,
        'query': query,
        'filtro_controlado': filtro_controlado,
    })


@requiere_roles(RolUsuario.ESTUDIANTE, RolUsuario.DOCENTE, RolUsuario.ADMIN)
def producto_create_view(request):
    """Registro de nuevo producto (CU-01)."""
    form = ProductoForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        producto = form.save()
        registrar_auditoria(
            accion='PRODUCTO_REGISTRADO',
            entidad='Producto',
            usuario=request.user,
            detalle={'codigo': producto.codigo, 'nombre': producto.nombre, 'es_controlado': producto.es_controlado},
            request=request
        )
        messages.success(request, f'Producto "{producto.nombre}" registrado exitosamente.')
        return redirect('inventario:producto_list')
    return render(request, 'inventario/producto_form.html', {'form': form, 'titulo': 'Registrar Nuevo Medicamento'})


@requiere_roles(RolUsuario.ESTUDIANTE, RolUsuario.DOCENTE, RolUsuario.ADMIN)
def producto_update_view(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    form = ProductoForm(request.POST or None, instance=producto)
    if request.method == 'POST' and form.is_valid():
        producto = form.save()
        registrar_auditoria(
            accion='PRODUCTO_ACTUALIZADO',
            entidad='Producto',
            usuario=request.user,
            detalle={'codigo': producto.codigo, 'nombre': producto.nombre},
            request=request
        )
        messages.success(request, f'Medicamento "{producto.nombre}" actualizado correctamente.')
        return redirect('inventario:producto_list')
    return render(request, 'inventario/producto_form.html', {
        'form': form,
        'titulo': f'Editar Medicamento: {producto.nombre}',
        'producto': producto
    })


@requiere_roles(RolUsuario.ESTUDIANTE, RolUsuario.DOCENTE, RolUsuario.ADMIN)
def lote_create_view(request):
    """
    Ingreso de Lote con validación de vencimiento > hoy (CU-02, Caso PF-03).
    """
    producto_id = request.GET.get('producto_id')
    initial_data = {}
    if producto_id:
        initial_data['producto'] = producto_id

    form = LoteForm(request.POST or None, initial=initial_data)
    if request.method == 'POST' and form.is_valid():
        lote = form.save()
        registrar_auditoria(
            accion='LOTE_INGRESADO',
            entidad='Lote',
            usuario=request.user,
            detalle={
                'producto': lote.producto.nombre,
                'codigo_lote': lote.codigo,
                'vencimiento': str(lote.fecha_vencimiento),
                'cantidad': lote.cantidad_inicial
            },
            request=request
        )
        messages.success(
            request,
            f'Lote "{lote.codigo}" de {lote.producto.nombre} ({lote.cantidad_inicial} u.) ingresado al inventario.'
        )
        return redirect('inventario:producto_list')
    return render(request, 'inventario/lote_form.html', {'form': form, 'titulo': 'Ingresar Nuevo Lote al Inventario'})


@requiere_roles(RolUsuario.ESTUDIANTE, RolUsuario.DOCENTE, RolUsuario.QUIMICO, RolUsuario.ADMIN)
def alertas_list_view(request):
    """Vista detallada de alertas de vencimiento y stock crítico (CU-04)."""
    alertas = obtener_alertas_inventario()
    return render(request, 'inventario/alertas.html', {'alertas': alertas})
