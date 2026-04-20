from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Pedido, EstadoPedido, HistorialEstadoPedido
from .serializers import PedidoListSerializer, PedidoDetalleSerializer


# ─── CLIENTE: Mis Pedidos ─────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mis_pedidos(request):
    """
    GET /api/v1/pedidos/
    Devuelve todos los pedidos del cliente autenticado, del más reciente al más antiguo.
    """
    try:
        cliente = request.user.cliente
    except AttributeError:
        return Response({'pedidos': [], 'total': 0})

    pedidos = (
        Pedido.objects
        .filter(cliente=cliente)
        .select_related('estado', 'direccion__ciudad__departamento')
        .prefetch_related('detalles__producto__imagenes')
        .order_by('-fecha_pedido')
    )
    serializer = PedidoListSerializer(pedidos, many=True)
    return Response({'pedidos': serializer.data, 'total': pedidos.count()})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def detalle_pedido(request, pedido_id):
    """
    GET /api/v1/pedidos/<pedido_id>/
    Devuelve el detalle completo de un pedido propio del cliente.
    """
    try:
        cliente = request.user.cliente
    except AttributeError:
        return Response({'detail': 'No tienes perfil de cliente.'}, status=status.HTTP_403_FORBIDDEN)

    pedido = get_object_or_404(
        Pedido.objects
        .select_related('estado', 'direccion__ciudad__departamento')
        .prefetch_related('detalles__producto__imagenes'),
        pedido_id=pedido_id,
        cliente=cliente,
    )
    return Response(PedidoDetalleSerializer(pedido).data)


# ─── ADMIN: Gestión de Pedidos ────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_pedidos_list(request):
    """
    GET /api/v1/admin/pedidos/?estado=1&search=&page=1
    Lista todos los pedidos con filtros opcionales. Solo para admins.
    """
    if not (request.user.is_staff or getattr(request.user, 'rol', None) and request.user.rol.nombre == 'admin'):
        return Response({'detail': 'No autorizado.'}, status=status.HTTP_403_FORBIDDEN)

    queryset = (
        Pedido.objects
        .select_related('estado', 'cliente__usuario', 'direccion__ciudad')
        .prefetch_related('detalles__producto')
        .order_by('-fecha_pedido')
    )

    # Filtro por estado
    estado_id = request.query_params.get('estado')
    if estado_id:
        queryset = queryset.filter(estado_id=estado_id)

    # Búsqueda por nombre de cliente o ID de pedido
    search = request.query_params.get('search', '').strip()
    if search:
        from django.db.models import Q
        queryset = queryset.filter(
            Q(pedido_id__icontains=search) |
            Q(cliente__usuario__nombre__icontains=search) |
            Q(cliente__usuario__email__icontains=search)
        )

    # Paginación simple
    page      = int(request.query_params.get('page', 1))
    page_size = 20
    total     = queryset.count()
    start     = (page - 1) * page_size
    pedidos   = queryset[start: start + page_size]

    serializer = PedidoListSerializer(pedidos, many=True)
    return Response({
        'pedidos':   serializer.data,
        'total':     total,
        'page':      page,
        'page_size': page_size,
        'pages':     (total + page_size - 1) // page_size,
    })


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def admin_pedido_cambiar_estado(request, pedido_id):
    """
    PATCH /api/v1/admin/pedidos/<pedido_id>/estado/
    Body: { "estado_id": 2 }
    Cambia el estado del pedido y registra el historial.
    """
    if not (request.user.is_staff or getattr(request.user, 'rol', None) and request.user.rol.nombre == 'admin'):
        return Response({'detail': 'No autorizado.'}, status=status.HTTP_403_FORBIDDEN)

    pedido = get_object_or_404(
        Pedido.objects.select_related('estado'),
        pedido_id=pedido_id,
    )

    estado_id = request.data.get('estado_id')
    if not estado_id:
        return Response({'detail': 'estado_id es requerido.'}, status=status.HTTP_400_BAD_REQUEST)

    nuevo_estado = get_object_or_404(EstadoPedido, estado_id=estado_id)
    pedido.estado = nuevo_estado
    pedido.save(update_fields=['estado_id'])

    # Registrar en historial
    HistorialEstadoPedido.objects.create(
        pedido=pedido,
        estado=nuevo_estado,
        cambiado_por=request.user,
    )

    return Response({
        'pedido_id':   pedido.pedido_id,
        'estado_id':   nuevo_estado.estado_id,
        'estado_nombre': nuevo_estado.nombre,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_estados_list(request):
    """GET /api/v1/admin/estados-pedido/ → lista todos los estados disponibles"""
    estados = EstadoPedido.objects.all().values('estado_id', 'nombre')
    return Response(list(estados))