from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from datetime import timedelta
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from .models import Pedido, EstadoPedido, HistorialEstadoPedido, DetallePedido
from catalogo.models import Producto
from usuarios.models import Usuario, Rol
from .serializers import PedidoListSerializer, PedidoDetalleSerializer


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

    pedidos = (
        Pedido.objects
        .filter(cliente=cliente)
        .select_related('estado', 'direccion__ciudad__departamento')
        .prefetch_related('detalles__producto__imagenes')
        .order_by('-fecha_pedido')
    )
    # PedidoDetalleSerializer hereda PedidoListSerializer y agrega:
    #   detalles, direccion_completa, notas
    serializer = PedidoDetalleSerializer(pedidos, many=True)
    return Response({'pedidos': serializer.data, 'total': pedidos.count()})


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
    if not (
        request.user.is_staff
        or (hasattr(request.user, 'rol') and request.user.rol.nombre == 'admin')
    ):
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
@permission_classes([IsAuthenticated])
def admin_dashboard(request):
    # GET /api/v1/admin/dashboard/
    # Resumen de metricas y listas para el dashboard de admin.
    if not (
        request.user.is_staff
        or (hasattr(request.user, 'rol') and request.user.rol.nombre == 'admin')
    ):
        return Response({'detail': 'No autorizado.'}, status=status.HTTP_403_FORBIDDEN)

    now = timezone.now()
    start_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    start_next_month = (start_month + timedelta(days=32)).replace(day=1)
    start_prev_month = (start_month - timedelta(days=1)).replace(day=1)

    pedidos_mes = Pedido.objects.filter(
        fecha_pedido__gte=start_month,
        fecha_pedido__lt=start_next_month,
    )
    pedidos_prev = Pedido.objects.filter(
        fecha_pedido__gte=start_prev_month,
        fecha_pedido__lt=start_month,
    )

    pedidos_mes_count = pedidos_mes.count()
    pedidos_prev_count = pedidos_prev.count()

    ingresos_mes = pedidos_mes.aggregate(total=Sum('total'))['total'] or 0
    ingresos_prev = pedidos_prev.aggregate(total=Sum('total'))['total'] or 0

    productos_activos = Producto.objects.filter(activo=True).count()
    clientes_total = Usuario.objects.filter(rol__nombre=Rol.CLIENTE).count()

    clientes_mes = Usuario.objects.filter(
        rol__nombre=Rol.CLIENTE,
        fecha_registro__gte=start_month,
        fecha_registro__lt=start_next_month,
    ).count()
    clientes_prev = Usuario.objects.filter(
        rol__nombre=Rol.CLIENTE,
        fecha_registro__gte=start_prev_month,
        fecha_registro__lt=start_month,
    ).count()

    def pct_delta(actual, prev):
        if prev == 0:
            return '+100%' if actual > 0 else '0'
        diff = (actual - prev) / prev * 100
        sign = '+' if diff > 0 else ''
        return f"{sign}{diff:.0f}%"

    def abs_delta(actual, prev):
        diff = actual - prev
        sign = '+' if diff > 0 else ''
        return f"{sign}{diff}"

    metrics = {
        'pedidos_mes': {
            'label': 'Pedidos este mes',
            'value': pedidos_mes_count,
            'delta': pct_delta(pedidos_mes_count, pedidos_prev_count),
        },
        'ingresos_mes': {
            'label': 'Ingresos (COP)',
            'value': float(ingresos_mes),
            'delta': pct_delta(float(ingresos_mes), float(ingresos_prev)),
        },
        'productos_activos': {
            'label': 'Productos activos',
            'value': productos_activos,
            'delta': '0',
        },
        'clientes': {
            'label': 'Clientes',
            'value': clientes_total,
            'delta': abs_delta(clientes_mes, clientes_prev),
        },
    }

    # Ventas ultimos 6 meses
    def add_months(dt, months):
        month = dt.month - 1 + months
        year = dt.year + month // 12
        month = month % 12 + 1
        return dt.replace(year=year, month=month, day=1, hour=0, minute=0, second=0, microsecond=0)

    start_6 = add_months(start_month, -5)
    ventas_qs = (
        Pedido.objects
        .filter(fecha_pedido__gte=start_6, fecha_pedido__lt=start_next_month)
        .annotate(mes=TruncMonth('fecha_pedido'))
        .values('mes')
        .annotate(ventas=Sum('total'))
        .order_by('mes')
    )
    ventas_map = {row['mes'].date(): float(row['ventas'] or 0) for row in ventas_qs}

    meses_labels = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun',
                    'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
    ventas_mes = []
    cursor = start_6
    for _ in range(6):
        key = cursor.date()
        ventas_mes.append({
            'mes': meses_labels[cursor.month - 1],
            'ventas': ventas_map.get(key, 0),
        })
        cursor = add_months(cursor, 1)

    # Pedidos recientes
    pedidos_recientes = (
        Pedido.objects
        .select_related('cliente__usuario', 'estado')
        .order_by('-fecha_pedido')[:5]
    )
    pedidos_data = [
        {
            'id': f"PED-{p.pedido_id:03d}",
            'cliente': p.cliente.usuario.nombre,
            'total': float(p.total),
            'estado': p.estado.nombre,
            'fecha': p.fecha_pedido,
        }
        for p in pedidos_recientes
    ]

    # Top productos por unidades
    top_qs = (
        DetallePedido.objects
        .values('producto__nombre')
        .annotate(ventas=Sum('cantidad'), ingresos=Sum('precio_total'))
        .order_by('-ventas')[:4]
    )
    top_productos = [
        {
            'nombre': row['producto__nombre'],
            'ventas': int(row['ventas'] or 0),
            'ingresos': float(row['ingresos'] or 0),
        }
        for row in top_qs
    ]

    # Alertas basicas
    pendientes_48h = Pedido.objects.filter(
        estado__nombre='Pendiente de preparación',
        fecha_pedido__lt=now - timedelta(hours=48),
    ).count()

    sin_imagen = Producto.objects.filter(activo=True).exclude(
        imagenes__es_principal=True
    ).distinct().count()

    alertas = []
    if pendientes_48h:
        alertas.append({
            'tipo': 'warning',
            'msg': f"{pendientes_48h} pedidos llevan mas de 48h en 'Pendiente de preparacion'",
        })
    if sin_imagen:
        alertas.append({
            'tipo': 'info',
            'msg': f"{sin_imagen} productos activos sin imagen principal",
        })

    periodo_label = f"{meses_labels[start_month.month - 1]} {start_month.year}"

    return Response({
        'periodo_label': periodo_label,
        'metrics': metrics,
        'ventas_mes': ventas_mes,
        'pedidos_recientes': pedidos_data,
        'top_productos': top_productos,
        'alertas': alertas,
    })
