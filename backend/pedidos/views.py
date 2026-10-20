from rest_framework import status
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from datetime import timedelta
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import Pedido, EstadoPedido, HistorialEstadoPedido, DetallePedido
from usuarios.models import Usuario, Rol
from .serializers import PedidoListSerializer, PedidoDetalleSerializer
from integrations.catalogo import get_catalog_products, get_catalog_summary
from integrations.identity import RemoteIdentityAuthentication, get_identity_dashboard
from integrations.pedidos import get_orders_dashboard


# ─── CLIENTE: Mis Pedidos ─────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mis_pedidos(request):
    """
    GET /api/v1/pedidos/
    Devuelve todos los pedidos del cliente autenticado, del más reciente al más antiguo.
    Incluye el detalle completo de ítems para que el frontend pueda mostrarlos
    al expandir cada tarjeta sin necesidad de una petición adicional.
    """
    try:
        cliente = request.user.cliente
    except AttributeError:
        return Response({'pedidos': [], 'total': 0})

    pedidos = list(
        Pedido.objects
        .filter(cliente=cliente)
        .select_related('estado', 'direccion__ciudad__departamento')
        .prefetch_related('detalles')
        .order_by('-fecha_pedido')
    )
    product_ids = {
        detalle.producto
        for pedido in pedidos
        for detalle in pedido.detalles.all()
    }
    catalog_products = get_catalog_products(product_ids)
    # PedidoDetalleSerializer hereda PedidoListSerializer y agrega:
    #   detalles, direccion_completa, notas
    serializer = PedidoDetalleSerializer(
        pedidos,
        many=True,
        context={'catalog_products': catalog_products},
    )
    return Response({'pedidos': serializer.data, 'total': len(pedidos)})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def detalle_pedido(request, pedido_id):
    """
    GET /api/v1/pedidos/<pedido_id>/
    Devuelve el detalle completo de un pedido propio del cliente.
    Usado por AdminPedidos y por cualquier vista que necesite un pedido individual.
    """
    try:
        cliente = request.user.cliente
    except AttributeError:
        return Response(
            {'detail': 'No tienes perfil de cliente.'},
            status=status.HTTP_403_FORBIDDEN,
        )

    pedido = get_object_or_404(
        Pedido.objects
        .select_related('estado', 'direccion__ciudad__departamento')
        .prefetch_related('detalles'),
        pedido_id=pedido_id,
        cliente=cliente,
    )
    catalog_products = get_catalog_products(
        detalle.producto for detalle in pedido.detalles.all()
    )
    return Response(
        PedidoDetalleSerializer(
            pedido,
            context={'catalog_products': catalog_products},
        ).data
    )


# ─── ADMIN: Gestión de Pedidos ────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_detalle_pedido(request, pedido_id):
    if not (
        request.user.is_staff
        or (hasattr(request.user, 'rol') and request.user.rol.nombre == 'admin')
    ):
        return Response({'detail': 'No autorizado.'}, status=status.HTTP_403_FORBIDDEN)

    pedido = get_object_or_404(
        Pedido.objects
        .select_related(
            'estado',
            'cliente__usuario',
            'direccion__ciudad__departamento',
        )
        .prefetch_related('detalles'),
        pedido_id=pedido_id,
    )
    catalog_products = get_catalog_products(
        detalle.producto for detalle in pedido.detalles.all()
    )
    return Response(
        PedidoDetalleSerializer(
            pedido,
            context={'catalog_products': catalog_products},
        ).data
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_pedidos_list(request):
    """
    GET /api/v1/admin/pedidos/?estado=1&search=&page=1
    Lista todos los pedidos con filtros opcionales. Solo para admins.
    """
    if not (
        request.user.is_staff
        or (hasattr(request.user, 'rol') and request.user.rol.nombre == 'admin')
    ):
        return Response({'detail': 'No autorizado.'}, status=status.HTTP_403_FORBIDDEN)

    queryset = (
        Pedido.objects
        .select_related('estado', 'cliente__usuario', 'direccion__ciudad')
        .prefetch_related('detalles')
        .order_by('-fecha_pedido')
    )

    # Filtro por estado
    estado_id = request.query_params.get('estado')
    if estado_id:
        queryset = queryset.filter(estado_id=estado_id)

    # Búsqueda por nombre de cliente, email o ID de pedido
    search = request.query_params.get('search', '').strip()
    if search:
        from django.db.models import Q
        queryset = queryset.filter(
            Q(pedido_id__icontains=search)
            | Q(cliente__usuario__nombre__icontains=search)
            | Q(cliente__usuario__email__icontains=search)
        )

    # Paginación simple
    page      = int(request.query_params.get('page', 1))
    page_size = 20
    total     = queryset.count()
    start     = (page - 1) * page_size
    pedidos   = queryset[start : start + page_size]

    serializer = PedidoListSerializer(pedidos, many=True)
    return Response({
        'pedidos':   serializer.data,
        'total':     total,
        'page':      page,
        'page_size': page_size,
        'pages':     max(1, (total + page_size - 1) // page_size),
    })


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def admin_pedido_cambiar_estado(request, pedido_id):
    """
    PATCH /api/v1/admin/pedidos/<pedido_id>/estado/
    Body: { "estado_id": 2 }
    Cambia el estado del pedido y registra el historial.
    """
    if not (
        request.user.is_staff
        or (hasattr(request.user, 'rol') and request.user.rol.nombre == 'admin')
    ):
        return Response({'detail': 'No autorizado.'}, status=status.HTTP_403_FORBIDDEN)

    pedido = get_object_or_404(
        Pedido.objects.select_related('estado'),
        pedido_id=pedido_id,
    )

    estado_id = request.data.get('estado_id')
    if not estado_id:
        return Response(
            {'detail': 'estado_id es requerido.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    nuevo_estado = get_object_or_404(EstadoPedido, estado_id=estado_id)
    pedido.estado = nuevo_estado
    pedido.save(update_fields=['estado_id'])

    # Registrar en historial
    HistorialEstadoPedido.objects.create(
        pedido       = pedido,
        estado       = nuevo_estado,
        cambiado_por = request.user,
    )

    return Response({
        'pedido_id':     pedido.pedido_id,
        'estado_id':     nuevo_estado.estado_id,
        'estado_nombre': nuevo_estado.nombre,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_estados_list(request):
    """GET /api/v1/admin/estados-pedido/ → lista todos los estados disponibles"""
    estados = EstadoPedido.objects.all().values('estado_id', 'nombre')
    return Response(list(estados))

@api_view(['GET'])
@authentication_classes([RemoteIdentityAuthentication])
@permission_classes([IsAuthenticated])
def admin_dashboard(request):
    # GET /api/v1/admin/dashboard/
    # Resumen de metricas y listas para el dashboard de admin.
    if not (
        request.user.is_staff
        or (hasattr(request.user, 'rol') and request.user.rol.nombre == 'admin')
    ):
        return Response({'detail': 'No autorizado.'}, status=status.HTTP_403_FORBIDDEN)

    orders_dashboard = get_orders_dashboard()
    identity_dashboard = get_identity_dashboard()
    catalog_summary = get_catalog_summary()
    productos_activos = catalog_summary['productos_activos']

    def abs_delta(actual, prev):
        diff = actual - prev
        sign = '+' if diff > 0 else ''
        return f"{sign}{diff}"

    metrics = {
        'pedidos_mes': {
            'label': 'Pedidos este mes',
            'value': orders_dashboard['pedidos_mes_count'],
            'delta': orders_dashboard['pct_pedidos'],
        },
        'ingresos_mes': {
            'label': 'Ingresos (COP)',
            'value': orders_dashboard['ingresos_mes'],
            'delta': orders_dashboard['pct_ingresos'],
        },
        'productos_activos': {
            'label': 'Productos activos',
            'value': productos_activos,
            'delta': '0',
        },
        'clientes': {
            'label': 'Clientes',
            'value': identity_dashboard['total_clientes'],
            'delta': abs_delta(
                identity_dashboard['clientes_mes'],
                identity_dashboard['clientes_mes_anterior'],
            ),
        },
    }

    sin_imagen = catalog_summary['productos_sin_imagen_principal']

    alertas = []
    if orders_dashboard['pendientes_48h']:
        alertas.append({
            'tipo': 'warning',
            'msg': f"{orders_dashboard['pendientes_48h']} pedidos llevan mas de 48h en 'Pendiente de preparacion'",
        })
    if sin_imagen:
        alertas.append({
            'tipo': 'info',
            'msg': f"{sin_imagen} productos activos sin imagen principal",
        })

    return Response({
        'periodo_label': orders_dashboard['periodo_label'],
        'metrics': metrics,
        'ventas_mes': orders_dashboard['ventas_mes'],
        'pedidos_recientes': orders_dashboard['pedidos_recientes'],
        'top_productos': orders_dashboard['top_productos'],
        'alertas': alertas,
    })
