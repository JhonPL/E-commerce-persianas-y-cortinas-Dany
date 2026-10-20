import logging

import requests
from django.conf import settings

from catalogo.models import Producto
from .models import NotificacionAdmin


logger = logging.getLogger(__name__)


def notificar_admin(pedido):
    endpoint = (
        settings.NOTIFICATION_SERVICE_URL.rstrip("/")
        + "/api/internal/notificaciones/pedidos/"
    )
    address = pedido.direccion
    details = list(pedido.detalles.all())
    products = Producto.objects.in_bulk(
        {detail.producto for detail in details},
        field_name="producto_id",
    )
    payload = {
        "pedido_id": pedido.pedido_id,
        "cliente_nombre": pedido.cliente.usuario.nombre,
        "cliente_email": pedido.cliente.usuario.email,
        "nombre_recibe": address.nombre_recibe,
        "direccion": ", ".join(
            part
            for part in (
                " ".join(part for part in (address.calle, address.numero) if part),
                address.barrio,
                address.ciudad.nombre,
                address.ciudad.departamento.nombre,
                address.complemento,
            )
            if part
        ),
        "total": str(pedido.total),
        "detalles": [
            {
                "producto_id": detail.producto,
                "producto_nombre": (
                    products[detail.producto].nombre
                    if detail.producto in products
                    else f"Producto #{detail.producto}"
                ),
                "cantidad": detail.cantidad,
                "ancho_cm": str(detail.ancho_cm),
                "alto_cm": str(detail.alto_cm),
                "precio_total": str(detail.precio_total),
            }
            for detail in details
        ],
    }
    try:
        response = requests.post(
            endpoint,
            json=payload,
            headers={
                "X-Internal-Service-Token": settings.INTERNAL_SERVICE_TOKEN,
            },
            timeout=settings.NOTIFICATION_SERVICE_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        result = response.json()
        if not isinstance(result, dict) or result.get("estado") not in (
            NotificacionAdmin.ENVIADO,
            NotificacionAdmin.FALLIDO,
            NotificacionAdmin.REINTENTANDO,
        ):
            raise ValueError("El servicio de notificaciones devolvió un estado inválido.")
        if result["estado"] == NotificacionAdmin.FALLIDO:
            logger.error(
                "Notification service recorded a failed delivery for order %s",
                pedido.pedido_id,
            )
        return result
    except (requests.RequestException, ValueError, TypeError) as exc:
        logger.exception(
            "Notification service unavailable for order %s",
            pedido.pedido_id,
        )
        NotificacionAdmin.objects.create(
            pedido=pedido,
            destinatario=getattr(
                settings,
                "ADMIN_EMAIL",
                "jhon.paternina302@gmail.com",
            ),
            estado=NotificacionAdmin.FALLIDO,
            error_detalle=str(exc),
        )
        return {
            "pedido_id": pedido.pedido_id,
            "estado": NotificacionAdmin.FALLIDO,
            "error_detalle": str(exc),
        }