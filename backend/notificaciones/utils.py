import logging

import requests
from django.conf import settings

from .models import NotificacionAdmin


logger = logging.getLogger(__name__)


def notificar_admin(pedido):
    endpoint = (
        settings.NOTIFICATION_SERVICE_URL.rstrip("/")
        + "/api/internal/notificaciones/pedidos/"
    )
    payload = {
        "pedido_id": pedido.pedido_id,
        "cliente_email": pedido.cliente.usuario.email,
        "total": str(pedido.total),
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