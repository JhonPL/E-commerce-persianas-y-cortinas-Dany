import base64
import hmac
import logging
from datetime import timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

import requests
from django.conf import settings
from django.db import transaction
from django.db.models import Q, Sum
from django.db.models.functions import TruncMonth
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .authentication import (
    InternalServiceTokenAuthentication,
    is_admin,
)
from .catalog import CatalogServiceUnavailable, get_catalog_products
from .models import (
    Ciudad,
    Departamento,
    DetallePedido,
    Direccion,
    EstadoPedido,
    HistorialEstadoPedido,
    Pedido,
)
from .serializers import PedidoDetalleSerializer, PedidoListSerializer


FULFILLMENT_STATES = (
    EstadoPedido.PENDIENTE,
    EstadoPedido.PREPARADO,
    EstadoPedido.ENVIADO,
)
ADMIN_MANAGED_STATES = (
    EstadoPedido.PREPARADO,
    EstadoPedido.ENVIADO,
)
ADMIN_STATE_TRANSITIONS = {
    EstadoPedido.PENDIENTE: (EstadoPedido.PREPARADO,),
    EstadoPedido.PREPARADO: (EstadoPedido.ENVIADO,),
    EstadoPedido.ENVIADO: (),
}
logger = logging.getLogger(__name__)
PAYMENT_TIMEOUT = timedelta(minutes=5)


class CheckoutAddressSerializer(serializers.Serializer):
    departamento = serializers.CharField(max_length=100)
    ciudad = serializers.CharField(max_length=100)
    nombre_recibe = serializers.CharField(max_length=100)
    barrio = serializers.CharField(max_length=100)
    calle = serializers.CharField(max_length=150, min_length=5)


class CartServiceUnavailable(Exception):
    pass


def _get_user_cart(request):
    authorization = request.headers.get("Authorization")
    if not authorization:
        raise AuthenticationFailed("Se requiere una sesión válida.")

    try:
        response = requests.get(
            settings.CART_SERVICE_URL.rstrip("/") + "/",
            headers={"Authorization": authorization},
            timeout=settings.SERVICE_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException as exc:
        raise CartServiceUnavailable from exc
    except ValueError as exc:
        raise CartServiceUnavailable from exc

    items = payload.get("items") if isinstance(payload, dict) else None
    if not isinstance(items, list):
        raise CartServiceUnavailable
    return items


def _calculate_checkout_items(items):
    if not items:
        raise ValidationError({"carrito": "El carrito está vacío."})

    prepared = []
    total = Decimal("0.00")
    for index, item in enumerate(items):
        try:
            product_id = int(item["producto_id"])
            quantity = int(item["cantidad"])
            width = Decimal(str(item["ancho_cm"]))
            height = Decimal(str(item["alto_cm"]))
            price = Decimal(str(item["precio_m2"]))
            if (
                product_id <= 0
                or quantity <= 0
                or width <= 0
                or height <= 0
                or price < 0
            ):
                raise ValueError
        except (KeyError, TypeError, ValueError, InvalidOperation) as exc:
            raise ValidationError(
                {"carrito": f"El artículo {index + 1} no tiene datos válidos."}
            ) from exc

        area = (width * height / Decimal("10000")).quantize(
            Decimal("0.0001"),
            rounding=ROUND_HALF_UP,
        )
        line_total = (area * price * quantity).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )
        total += line_total
        prepared.append(
            {
                "producto": product_id,
                "cantidad": quantity,
                "ancho_cm": width,
                "alto_cm": height,
                "area_m2": area,
                "precio_m2": price,
                "precio_total": line_total,
            }
        )
    return prepared, total.quantize(Decimal("0.01"))


def _approved_order_payload(order):
    catalog_products = get_catalog_products(
        detail.producto for detail in order.detalles.all()
    )
    return {
        "pedido_id": order.pedido_id,
        "cliente_nombre": order.cliente_nombre,
        "cliente_email": order.cliente_email,
        "estado_pedido": order.estado.nombre,
        "estado_pago": (
            "Aprobado por el simulador; no se realizó un cobro real"
        ),
        "metodo_pago": "Tarjeta de prueba (simulación)",
        "importe_pagado": str(order.total),
        "saldo_pendiente": "0.00",
        "nombre_recibe": order.direccion.nombre_recibe,
        "direccion": ", ".join(
            part
            for part in (
                order.direccion.calle,
                order.direccion.barrio,
                order.direccion.ciudad.nombre,
                order.direccion.ciudad.departamento.nombre,
            )
            if part
        ),
        "total": str(order.total),
        "observaciones": order.notas or "",
        "detalles": [
            {
                "producto_id": item.producto,
                "producto_nombre": item.producto_nombre,
                "categoria_nombre": catalog_products[item.producto].get(
                    "categoria_nombre",
                    "",
                ),
                "descripcion": catalog_products[item.producto].get(
                    "descripcion",
                    "",
                ) or "",
                "cantidad": item.cantidad,
                "ancho_cm": str(item.ancho_cm),
                "alto_cm": str(item.alto_cm),
                "precio_total": str(item.precio_total),
            }
            for item in order.detalles.all()
        ],
    }


class InvoiceGenerationError(Exception):
    def __init__(self, message, status_code=status.HTTP_503_SERVICE_UNAVAILABLE):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _generate_demo_invoice(order, payload=None):
    token = settings.INTERNAL_SERVICE_TOKEN
    if not token:
        logger.error(
            "Order %s was paid but its billing token is not configured.",
            order.pedido_id,
        )
        raise InvoiceGenerationError(
            "Falta configurar INTERNAL_SERVICE_TOKEN en el servicio de pedidos."
        )

    try:
        data = payload if payload is not None else _approved_order_payload(order)
    except CatalogServiceUnavailable as exc:
        logger.exception(
            "Order %s was paid but its catalog details could not be loaded.",
            order.pedido_id,
        )
        raise InvoiceGenerationError(
            "No fue posible cargar los detalles del catálogo para la factura."
        ) from exc

    try:
        response = requests.post(
            (
                f"{settings.BILLING_SERVICE_URL}"
                "/api/internal/facturas/demo-pdf/"
            ),
            json=data,
            headers={"X-Internal-Service-Token": token},
            timeout=settings.SERVICE_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        if (
            response.headers.get("Content-Type", "").split(";")[0]
            != "application/pdf"
            or not response.content.startswith(b"%PDF-")
        ):
            raise ValueError("Billing devolvió un comprobante PDF inválido.")
    except requests.Timeout as exc:
        logger.exception("Timeout conectando a billing para pedido %s", order.pedido_id)
        raise InvoiceGenerationError(
            f"Tiempo de espera agotado al conectar con el servicio de facturación ({settings.BILLING_SERVICE_URL}). Es posible que el contenedor esté iniciando."
        ) from exc
    except requests.RequestException as exc:
        logger.exception(
            "Order %s was paid but its demo invoice could not be generated: %s",
            order.pedido_id,
            exc,
        )
        status_code = getattr(getattr(exc, "response", None), "status_code", None)
        if status_code in (401, 403):
            detail = f"Facturación rechazó la autenticación interna (HTTP {status_code}). Verifica que INTERNAL_SERVICE_TOKEN coincida en pedidos y facturación."
        else:
            detail = f"Error al comunicarse con el servicio de facturación ({settings.BILLING_SERVICE_URL}): {exc}"
        raise InvoiceGenerationError(detail) from exc
    except ValueError as exc:
        logger.exception(
            "Order %s was paid but its demo invoice could not be generated: %s",
            order.pedido_id,
            exc,
        )
        raise InvoiceGenerationError(str(exc)) from exc

    return {
        "numero_factura": response.headers.get(
            "X-Invoice-Number",
            f"DEMO-{order.pedido_id:06d}",
        ),
        "pdf_base64": base64.b64encode(response.content).decode("ascii"),
    }


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def descargar_factura(request, pedido_id):
    if is_admin(request.user):
        order = get_object_or_404(_order_queryset(), pedido_id=pedido_id)
    elif getattr(request.user, "rol_nombre", None) == "cliente":
        order = get_object_or_404(
            _order_queryset(),
            pedido_id=pedido_id,
            usuario=request.user.usuario_id,
        )
    else:
        return Response(
            {"detail": "No tienes permiso para descargar este documento."},
            status=status.HTTP_403_FORBIDDEN,
        )

    if order.estado.nombre not in FULFILLMENT_STATES:
        return Response(
            {"detail": "El documento estará disponible cuando el pago sea aprobado."},
            status=status.HTTP_409_CONFLICT,
        )

    try:
        invoice = _generate_demo_invoice(order)
    except InvoiceGenerationError as exc:
        return Response(
            {"detail": exc.message},
            status=exc.status_code,
        )

    response = HttpResponse(
        base64.b64decode(invoice["pdf_base64"], validate=True),
        content_type="application/pdf",
    )
    response["Content-Disposition"] = (
        f'attachment; filename="{invoice["numero_factura"]}.pdf"'
    )
    response["Cache-Control"] = "private, no-store"
    return response


def _notify_payment_approved(order):
    token = settings.INTERNAL_SERVICE_TOKEN
    if not token:
        logger.error(
            "Order %s was paid but its notification token is not configured.",
            order.pedido_id,
        )
        return "fallido"

    try:
        payload = _approved_order_payload(order)
    except CatalogServiceUnavailable:
        logger.exception(
            "Order %s was paid but its catalog details could not be loaded.",
            order.pedido_id,
        )
        return "fallido"

    try:
        invoice = _generate_demo_invoice(order, payload)
    except InvoiceGenerationError:
        return "fallido"

    payload.update(invoice)
    try:
        response = requests.post(
            (
                f"{settings.NOTIFICATIONS_SERVICE_URL}"
                "/api/internal/notificaciones/pedidos/"
            ),
            json=payload,
            headers={"X-Internal-Service-Token": token},
            timeout=settings.SERVICE_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        result = response.json()
    except (requests.RequestException, ValueError):
        logger.exception(
            "Order %s was paid but its notification could not be delivered.",
            order.pedido_id,
        )
        return "fallido"

    if (
        not isinstance(result, dict)
        or result.get("pedido_id") != order.pedido_id
        or result.get("admin_estado") != "enviado"
        or result.get("cliente_estado") != "enviado"
    ):
        logger.error(
            "Order %s payment notification delivery was incomplete.",
            order.pedido_id,
        )
        return "fallido"
    return "enviado"


def _notify_order_status_changed(order, previous_state, history_id):
    token = settings.INTERNAL_SERVICE_TOKEN
    if not token:
        logger.error(
            "Order %s state changed but its notification token is not configured.",
            order.pedido_id,
        )
        return "fallido"

    try:
        response = requests.post(
            (
                f"{settings.NOTIFICATIONS_SERVICE_URL}"
                "/api/internal/notificaciones/pedidos/estado/"
            ),
            json={
                "pedido_id": order.pedido_id,
                "historial_id": history_id,
                "cliente_nombre": order.cliente_nombre,
                "cliente_email": order.cliente_email,
                "nombre_recibe": order.direccion.nombre_recibe,
                "direccion": ", ".join(
                    part
                    for part in (
                        order.direccion.calle,
                        order.direccion.barrio,
                        order.direccion.ciudad.nombre,
                        order.direccion.ciudad.departamento.nombre,
                    )
                    if part
                ),
                "estado_anterior": previous_state,
                "estado_nuevo": order.estado.nombre,
            },
            headers={"X-Internal-Service-Token": token},
            timeout=settings.SERVICE_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        result = response.json()
    except (requests.RequestException, ValueError):
        logger.exception(
            "Order %s state changed but its customer notification failed.",
            order.pedido_id,
        )
        return "fallido"

    if (
        not isinstance(result, dict)
        or result.get("pedido_id") != order.pedido_id
        or result.get("estado") not in ("enviado", "reintentando")
    ):
        logger.error(
            "Order %s state notification delivery was incomplete.",
            order.pedido_id,
        )
        return "fallido"
    return result["estado"]


def _expire_unpaid_order(order_id, now=None):
    now = now or timezone.now()
    with transaction.atomic():
        order = (
            Pedido.objects.select_for_update()
            .select_related("estado")
            .filter(pedido_id=order_id)
            .first()
        )
        if (
            order is None
            or order.estado.nombre != "Pendiente de pago"
            or order.fecha_pedido > now - PAYMENT_TIMEOUT
        ):
            return None

        rejected_state, _ = EstadoPedido.objects.get_or_create(
            nombre="Pago rechazado",
        )
        order.estado = rejected_state
        order.save(update_fields=["estado"])
        history = HistorialEstadoPedido.objects.create(
            pedido=order,
            estado=rejected_state,
            cambiado_por=0,
            notas_cambio=(
                "Pago simulado rechazado automáticamente: venció el plazo de "
                "cinco minutos."
            ),
        )

    notification_status = _notify_order_status_changed(
        order,
        "Pendiente de pago",
        history.historial_id,
    )
    return order, notification_status


def _expire_due_unpaid_orders(now=None):
    now = now or timezone.now()
    expired_ids = list(
        Pedido.objects.filter(
            estado__nombre="Pendiente de pago",
            fecha_pedido__lte=now - PAYMENT_TIMEOUT,
        )
        .order_by("pedido_id")
        .values_list("pedido_id", flat=True)
    )
    return sum(
        _expire_unpaid_order(order_id, now=now) is not None
        for order_id in expired_ids
    )


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def expire_unpaid_orders_scheduled(request):
    expected_token = settings.EXPIRATION_JOB_TOKEN
    if not expected_token:
        return Response(
            {"detail": "Order-expiration job is not configured."},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    supplied_token = request.headers.get("X-Expiration-Job-Token", "")
    if not hmac.compare_digest(supplied_token, expected_token):
        return Response(
            {"detail": "Invalid scheduler credential."},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    expired_count = _expire_due_unpaid_orders()
    return Response({"rejected": expired_count}, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def checkout(request):
    address_serializer = CheckoutAddressSerializer(data=request.data.get("direccion", {}))
    address_serializer.is_valid(raise_exception=True)

    try:
        cart_items = _get_user_cart(request)
    except CartServiceUnavailable as exc:
        return Response(
            {"detail": "No fue posible obtener el carrito para crear el pedido."},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    order_items, total = _calculate_checkout_items(cart_items)
    if total <= 0:
        raise ValidationError({"carrito": "El total del pedido debe ser mayor a cero."})
    catalog_products = get_catalog_products(
        (item["producto"] for item in order_items),
    )
    for item in order_items:
        item["producto_nombre"] = catalog_products[item["producto"]]["nombre"]

    address_data = address_serializer.validated_data
    with transaction.atomic():
        department, _ = Departamento.objects.get_or_create(
            nombre__iexact=address_data["departamento"],
            defaults={"nombre": address_data["departamento"].strip()},
        )
        city, _ = Ciudad.objects.get_or_create(
            departamento=department,
            nombre__iexact=address_data["ciudad"],
            defaults={"nombre": address_data["ciudad"].strip()},
        )
        address = Direccion.objects.create(
            usuario=request.user.usuario_id,
            ciudad=city,
            nombre_recibe=address_data["nombre_recibe"].strip(),
            barrio=address_data["barrio"].strip(),
            calle=address_data["calle"].strip(),
            numero="",
            complemento="",
        )
        pending_state, _ = EstadoPedido.objects.get_or_create(
            nombre="Pendiente de pago",
        )
        order = Pedido.objects.create(
            usuario=request.user.usuario_id,
            cliente_nombre=request.user.nombre or request.user.email,
            cliente_email=request.user.email,
            direccion=address,
            estado=pending_state,
            total=total,
        )
        DetallePedido.objects.bulk_create(
            [
                DetallePedido(pedido=order, **item)
                for item in order_items
            ]
        )
        HistorialEstadoPedido.objects.create(
            pedido=order,
            estado=pending_state,
            cambiado_por=request.user.usuario_id,
            notas_cambio="Pedido creado; pago simulado pendiente.",
        )

    return Response(
        {
            "pedido_id": order.pedido_id,
            "total": str(order.total),
            "estado": pending_state.nombre,
            "simulacion": True,
        },
        status=status.HTTP_201_CREATED,
    )


def _order_queryset():
    return Pedido.objects.select_related(
        "estado",
        "direccion__ciudad__departamento",
    ).prefetch_related("detalles")


def _serialize_order_details(orders):
    product_ids = {
        detail.producto
        for order in orders
        for detail in order.detalles.all()
    }
    catalog_products = get_catalog_products(product_ids)
    return PedidoDetalleSerializer(
        orders,
        many=True,
        context={"catalog_products": catalog_products},
    ).data


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def mis_pedidos(request):
    orders = list(
        _order_queryset()
        .filter(usuario=request.user.usuario_id)
        .order_by("-fecha_pedido")
    )
    return Response(
        {
            "pedidos": _serialize_order_details(orders),
            "total": len(orders),
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def detalle_pedido(request, pedido_id):
    if getattr(request.user, "rol_nombre", None) != "cliente":
        return Response(
            {"detail": "No tienes perfil de cliente."},
            status=status.HTTP_403_FORBIDDEN,
        )
    order = get_object_or_404(
        _order_queryset(),
        pedido_id=pedido_id,
        usuario=request.user.usuario_id,
    )
    return Response(_serialize_order_details([order])[0])


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def admin_detalle_pedido(request, pedido_id):
    if not is_admin(request.user):
        return Response(
            {"detail": "No autorizado."},
            status=status.HTTP_403_FORBIDDEN,
        )
    order = get_object_or_404(_order_queryset(), pedido_id=pedido_id)
    return Response(_serialize_order_details([order])[0])


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def admin_pedidos_list(request):
    if not is_admin(request.user):
        return Response(
            {"detail": "No autorizado."},
            status=status.HTTP_403_FORBIDDEN,
        )

    queryset = _order_queryset().filter(
        estado__nombre__in=FULFILLMENT_STATES,
    ).order_by("-fecha_pedido")
    state_id = request.query_params.get("estado")
    if state_id:
        queryset = queryset.filter(estado_id=state_id)

    search = request.query_params.get("search", "").strip()
    if search:
        search_filter = Q(
            cliente_nombre__icontains=search,
        ) | Q(cliente_email__icontains=search)
        if search.isdecimal():
            search_filter |= Q(pedido_id=int(search))
        queryset = queryset.filter(search_filter)

    try:
        page = max(1, int(request.query_params.get("page", 1)))
    except (TypeError, ValueError) as exc:
        raise ValidationError({"page": "page debe ser un entero positivo."}) from exc

    page_size = 20
    total = queryset.count()
    orders = list(queryset[(page - 1) * page_size : page * page_size])
    serializer = PedidoListSerializer(orders, many=True)
    return Response(
        {
            "pedidos": serializer.data,
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": max(1, (total + page_size - 1) // page_size),
        }
    )


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def admin_pedido_cambiar_estado(request, pedido_id):
    if not is_admin(request.user):
        return Response(
            {"detail": "No autorizado."},
            status=status.HTTP_403_FORBIDDEN,
        )

    state_id = request.data.get("estado_id")
    if not state_id:
        return Response(
            {"detail": "estado_id es requerido."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        state_id = int(state_id)
    except (TypeError, ValueError) as exc:
        raise ValidationError({"estado_id": "Debe ser un identificador entero."}) from exc

    new_state = get_object_or_404(EstadoPedido, estado_id=state_id)
    if new_state.nombre not in ADMIN_MANAGED_STATES:
        raise ValidationError(
            {"estado_id": "El administrador solo puede marcar pedidos como preparados o enviados."}
        )

    with transaction.atomic():
        order = get_object_or_404(
            Pedido.objects.select_for_update().select_related("estado"),
            pedido_id=pedido_id,
        )
        if order.estado.nombre not in FULFILLMENT_STATES:
            raise ValidationError(
                {"pedido_id": "Solo los pedidos con pago aprobado pueden gestionarse."}
            )
        if new_state.nombre not in ADMIN_STATE_TRANSITIONS[order.estado.nombre]:
            raise ValidationError(
                {"estado_id": "El pedido solo puede avanzar de pendiente a preparado y luego a enviado."}
            )
        previous_state = order.estado.nombre
        order.estado = new_state
        order.save(update_fields=["estado"])
        history = HistorialEstadoPedido.objects.create(
            pedido=order,
            estado=new_state,
            cambiado_por=request.user.usuario_id,
        )

    notification_status = _notify_order_status_changed(
        order,
        previous_state,
        history.historial_id,
    )
    return Response(
        {
            "pedido_id": order.pedido_id,
            "estado_id": new_state.estado_id,
            "estado_nombre": new_state.nombre,
            "notificacion_estado": notification_status,
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def admin_estados_list(request):
    if not is_admin(request.user):
        return Response(
            {"detail": "No autorizado."},
            status=status.HTTP_403_FORBIDDEN,
        )
    states = EstadoPedido.objects.filter(
        nombre__in=FULFILLMENT_STATES,
    ).values("estado_id", "nombre")
    return Response(list(states))


def _add_months(value, months):
    month = value.month - 1 + months
    year = value.year + month // 12
    month = month % 12 + 1
    return value.replace(
        year=year,
        month=month,
        day=1,
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )


def _dashboard_data():
    now = timezone.now()
    start_month = now.replace(
        day=1,
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )
    start_next_month = _add_months(start_month, 1)
    start_prev_month = _add_months(start_month, -1)

    orders_month = Pedido.objects.filter(
        estado__nombre__in=FULFILLMENT_STATES,
        fecha_pedido__gte=start_month,
        fecha_pedido__lt=start_next_month,
    )
    orders_prev = Pedido.objects.filter(
        estado__nombre__in=FULFILLMENT_STATES,
        fecha_pedido__gte=start_prev_month,
        fecha_pedido__lt=start_month,
    )
    income_month = orders_month.aggregate(total=Sum("total"))["total"] or 0
    income_prev = orders_prev.aggregate(total=Sum("total"))["total"] or 0

    def pct_delta(actual, previous):
        if previous == 0:
            return "+100%" if actual > 0 else "0"
        difference = (actual - previous) / previous * 100
        sign = "+" if difference > 0 else ""
        return f"{sign}{difference:.0f}%"

    start_six_months = _add_months(start_month, -5)
    sales_rows = (
        Pedido.objects.filter(
            estado__nombre__in=FULFILLMENT_STATES,
            fecha_pedido__gte=start_six_months,
            fecha_pedido__lt=start_next_month,
        )
        .annotate(month=TruncMonth("fecha_pedido"))
        .values("month")
        .annotate(sales=Sum("total"))
        .order_by("month")
    )
    sales_by_month = {
        row["month"].date(): float(row["sales"] or 0)
        for row in sales_rows
    }
    month_labels = [
        "Ene",
        "Feb",
        "Mar",
        "Abr",
        "May",
        "Jun",
        "Jul",
        "Ago",
        "Sep",
        "Oct",
        "Nov",
        "Dic",
    ]
    monthly_sales = []
    cursor = start_six_months
    for _ in range(6):
        monthly_sales.append(
            {
                "mes": month_labels[cursor.month - 1],
                "ventas": sales_by_month.get(cursor.date(), 0),
            }
        )
        cursor = _add_months(cursor, 1)

    recent_orders = Pedido.objects.filter(
        estado__nombre__in=FULFILLMENT_STATES,
    ).select_related("estado").order_by(
        "-fecha_pedido"
    )[:5]
    recent_data = [
        {
            "id": f"PED-{order.pedido_id:03d}",
            "cliente": order.cliente_nombre,
            "total": float(order.total),
            "estado": order.estado.nombre,
            "fecha": order.fecha_pedido,
        }
        for order in recent_orders
    ]

    top_rows = list(
        DetallePedido.objects.filter(
            pedido__estado__nombre__in=FULFILLMENT_STATES,
        ).values("producto")
        .annotate(sales=Sum("cantidad"), income=Sum("precio_total"))
        .order_by("-sales")[:4]
    )
    products = get_catalog_products(row["producto"] for row in top_rows)
    top_products = [
        {
            "nombre": products[row["producto"]]["nombre"],
            "ventas": int(row["sales"] or 0),
            "ingresos": float(row["income"] or 0),
        }
        for row in top_rows
    ]
    pending_orders = Pedido.objects.filter(
        estado__nombre=EstadoPedido.PENDIENTE,
        fecha_pedido__lt=now - timedelta(hours=48),
    ).count()

    return {
        "periodo_label": f"{month_labels[start_month.month - 1]} {start_month.year}",
        "pedidos_mes_count": orders_month.count(),
        "pedidos_prev_count": orders_prev.count(),
        "ingresos_mes": float(income_month),
        "ingresos_prev": float(income_prev),
        "ventas_mes": monthly_sales,
        "pedidos_recientes": recent_data,
        "top_productos": top_products,
        "pendientes_48h": pending_orders,
        "pct_pedidos": pct_delta(orders_month.count(), orders_prev.count()),
        "pct_ingresos": pct_delta(float(income_month), float(income_prev)),
    }


@api_view(["GET"])
@authentication_classes([InternalServiceTokenAuthentication])
@permission_classes([IsAuthenticated])
def internal_dashboard(request):
    if not getattr(request.user, "is_internal_service", False):
        raise AuthenticationFailed("Se requiere autenticación de servicio.")
    return Response(_dashboard_data())


@api_view(["GET"])
@authentication_classes([InternalServiceTokenAuthentication])
@permission_classes([IsAuthenticated])
def internal_payment_context(request, pedido_id):
    if not getattr(request.user, "is_internal_service", False):
        raise AuthenticationFailed("Se requiere autenticación de servicio.")
    expired_order = _expire_unpaid_order(pedido_id)
    if expired_order is not None:
        return Response(
            {
                "detail": (
                    "El plazo de pago de cinco minutos venció y el pedido fue "
                    "rechazado."
                )
            },
            status=status.HTTP_409_CONFLICT,
        )
    order = get_object_or_404(
        Pedido.objects.select_related("estado"),
        pedido_id=pedido_id,
    )
    if (
        order.fecha_pedido <= timezone.now() - PAYMENT_TIMEOUT
        and order.estado.nombre == "Pago rechazado"
    ):
        return Response(
            {"detail": "El plazo de pago de cinco minutos venció."},
            status=status.HTTP_409_CONFLICT,
        )
    if order.estado.nombre == "Pendiente de preparación":
        return Response(
            {"detail": "El pedido ya tiene un pago aprobado."},
            status=status.HTTP_409_CONFLICT,
        )
    return Response(
        {
            "pedido_id": order.pedido_id,
            "usuario_id": order.usuario,
            "total": str(order.total),
            "estado": order.estado.nombre,
        }
    )


@api_view(["POST"])
@authentication_classes([InternalServiceTokenAuthentication])
@permission_classes([IsAuthenticated])
def internal_payment_result(request, pedido_id):
    if not getattr(request.user, "is_internal_service", False):
        raise AuthenticationFailed("Se requiere autenticación de servicio.")

    outcome = request.data.get("outcome")
    reference = request.data.get("payment_reference")
    amount = request.data.get("amount")
    if outcome not in ("approved", "declined") or not reference:
        raise ValidationError(
            {"detail": "El resultado y la referencia de pago son obligatorios."}
        )
    try:
        amount = Decimal(str(amount)).quantize(Decimal("0.01"))
    except (TypeError, ValueError, InvalidOperation) as exc:
        raise ValidationError({"amount": "El importe del pago no es válido."}) from exc

    expired = False
    duplicate = False
    notification_history_id = None
    previous_state = None
    with transaction.atomic():
        order = get_object_or_404(
            Pedido.objects.select_for_update().select_related("estado"),
            pedido_id=pedido_id,
        )
        if amount != order.total:
            raise ValidationError(
                {"amount": "El importe no coincide con el total del pedido."}
            )
        if order.estado.nombre == "Pendiente de preparación":
            if order.referencia_pago == reference and outcome == "approved":
                duplicate = True
            else:
                return Response(
                    {"detail": "El pedido ya tiene un pago aprobado."},
                    status=status.HTTP_409_CONFLICT,
                )
        elif (
            order.estado.nombre == "Pago rechazado"
            and order.fecha_pedido <= timezone.now() - PAYMENT_TIMEOUT
        ):
            return Response(
                {"detail": "El plazo de pago de cinco minutos venció."},
                status=status.HTTP_409_CONFLICT,
            )
        elif (
            order.estado.nombre == "Pendiente de pago"
            and order.fecha_pedido <= timezone.now() - PAYMENT_TIMEOUT
        ):
            previous_state = order.estado.nombre
            next_state, _ = EstadoPedido.objects.get_or_create(
                nombre="Pago rechazado",
            )
            order.estado = next_state
            order.save(update_fields=["estado"])
            history = HistorialEstadoPedido.objects.create(
                pedido=order,
                estado=next_state,
                cambiado_por=0,
                notas_cambio=(
                    "Pago simulado rechazado automáticamente: venció el plazo de "
                    "cinco minutos."
                ),
            )
            notification_history_id = history.historial_id
            expired = True
        else:
            previous_state = order.estado.nombre
            next_state_name = (
                "Pendiente de preparación" if outcome == "approved" else "Pago rechazado"
            )
            if (
                order.referencia_pago == reference
                and order.estado.nombre == next_state_name
            ):
                duplicate = True
            else:
                next_state, _ = EstadoPedido.objects.get_or_create(
                    nombre=next_state_name,
                )
                order.estado = next_state
                order.referencia_pago = str(reference)
                order.save(update_fields=["estado", "referencia_pago"])
                history = HistorialEstadoPedido.objects.create(
                    pedido=order,
                    estado=next_state,
                    cambiado_por=order.usuario,
                    notas_cambio=(
                        "Pago aprobado por el simulador."
                        if outcome == "approved"
                        else "Pago rechazado por el simulador."
                    ),
                )
                notification_history_id = history.historial_id

    if expired:
        notification_status = _notify_order_status_changed(
            order,
            previous_state,
            notification_history_id,
        )
        return Response(
            {
                "detail": (
                    "El plazo de pago de cinco minutos venció y el pedido fue "
                    "rechazado."
                ),
                "notificacion": notification_status,
            },
            status=status.HTTP_409_CONFLICT,
        )

    if outcome == "approved":
        notification_status = _notify_payment_approved(order)
    elif not duplicate:
        notification_status = _notify_order_status_changed(
            order,
            previous_state,
            notification_history_id,
        )
    else:
        notification_status = None

    return Response(
        {
            "pedido_id": order.pedido_id,
            "estado": order.estado.nombre,
            "payment_reference": str(reference),
            "duplicate": duplicate,
            "notificacion": notification_status,
        }
    )


@api_view(["GET"])
@authentication_classes([InternalServiceTokenAuthentication])
@permission_classes([IsAuthenticated])
def check_product_references(request, product_id):
    if not getattr(request.user, "is_internal_service", False):
        raise AuthenticationFailed("Se requiere autenticación de servicio.")
    if DetallePedido.objects.filter(producto=product_id).exists():
        return Response(
            {"detail": "El producto está asociado a pedidos existentes."},
            status=status.HTTP_409_CONFLICT,
        )
    return Response({"referenced": False})
