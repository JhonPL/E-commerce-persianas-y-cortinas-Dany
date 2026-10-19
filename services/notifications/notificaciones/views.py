import logging
import smtplib
import socket
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.db.models import F
from django.core.mail import send_mail
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import NotificacionAdmin
from .permissions import EsServicioInterno
from .serializers import PedidoApprovedSerializer


logger = logging.getLogger(__name__)


class PedidoApprovedNotificationView(APIView):
    permission_classes = [EsServicioInterno]

    def post(self, request):
        serializer = PedidoApprovedSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        pedido_id = data["pedido_id"]
        evento_id = f"pedido:{pedido_id}:payment-approved"
        destinatario = settings.ADMIN_EMAIL
        defaults = {
            "pedido_id": pedido_id,
            "destinatario": destinatario,
            "estado": NotificacionAdmin.PENDIENTE,
            "intentos": 0,
        }
        with transaction.atomic():
            notification, _ = NotificacionAdmin.objects.get_or_create(
                evento_id=evento_id,
                defaults=defaults,
            )
            notification = NotificacionAdmin.objects.select_for_update().get(
                pk=notification.pk
            )
            if notification.estado == NotificacionAdmin.ENVIADO:
                return Response(
                    {
                        "notif_id": notification.pk,
                        "pedido_id": notification.pedido_id,
                        "estado": notification.estado,
                        "intentos": notification.intentos,
                        "duplicate": True,
                    }
                )
            if (
                notification.estado == NotificacionAdmin.REINTENTANDO
                and notification.actualizado_en
                >= timezone.now() - timedelta(seconds=30)
            ):
                return Response(
                    {
                        "notif_id": notification.pk,
                        "pedido_id": notification.pedido_id,
                        "estado": notification.estado,
                        "intentos": notification.intentos,
                        "duplicate": True,
                    }
                )
            notification.estado = NotificacionAdmin.REINTENTANDO
            notification.intentos = F("intentos") + 1
            notification.error_detalle = None
            notification.save(
                update_fields=[
                    "estado",
                    "intentos",
                    "error_detalle",
                    "actualizado_en",
                ]
            )
            notification.refresh_from_db(fields=["intentos"])

        subject = f"🛒 Nuevo pedido #{pedido_id} — ${data['total']:,.0f} COP"
        message = (
            "Se realizó un nuevo pedido.\n\n"
            f"Pedido ID: {pedido_id}\n"
            f"Cliente: {data['cliente_email']}\n"
            f"Total: ${data['total']:,.0f} COP\n"
        )
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[destinatario],
                fail_silently=False,
            )
        except (smtplib.SMTPException, OSError, socket.timeout) as exc:
            logger.exception(
                "Failed to send approved-order notification for order %s",
                pedido_id,
            )
            notification.estado = NotificacionAdmin.FALLIDO
            notification.error_detalle = str(exc)
            notification.save(
                update_fields=["estado", "error_detalle", "actualizado_en"]
            )
        else:
            notification.estado = NotificacionAdmin.ENVIADO
            notification.error_detalle = None
            notification.save(
                update_fields=["estado", "error_detalle", "actualizado_en"]
            )

        return Response(
            {
                "notif_id": notification.pk,
                "pedido_id": notification.pedido_id,
                "estado": notification.estado,
                "intentos": notification.intentos,
                "duplicate": False,
            },
            status=status.HTTP_200_OK,
        )
