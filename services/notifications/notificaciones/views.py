import logging
import smtplib
import socket
from datetime import timedelta

from django.conf import settings
from django.core.mail import EmailMessage
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import NotificacionAdmin
from .permissions import EsServicioInterno
from .serializers import (
    ContactMessageSerializer,
    PedidoApprovedSerializer,
    PedidoCreatedSerializer,
    PedidoStatusChangedSerializer,
)


logger = logging.getLogger(__name__)


def _admin_recipient():
    recipient = settings.ADMIN_EMAIL.strip()
    sender_addresses = {
        settings.DEFAULT_FROM_EMAIL.strip().casefold(),
        settings.EMAIL_HOST_USER.strip().casefold(),
    }
    if not recipient or recipient.casefold() in sender_addresses:
        logger.error(
            "Administrative notification recipient must differ from the SMTP sender."
        )
        return None
    return recipient


def _send_order_email(
    *,
    evento_id,
    pedido_id,
    destinatario,
    subject,
    message,
    reply_to=None,
):
    with transaction.atomic():
        notification, _ = NotificacionAdmin.objects.get_or_create(
            evento_id=evento_id,
            defaults={
                "pedido_id": pedido_id,
                "destinatario": destinatario,
                "estado": NotificacionAdmin.PENDIENTE,
                "intentos": 0,
            },
        )
        notification = NotificacionAdmin.objects.select_for_update().get(
            pk=notification.pk
        )
        if notification.estado == NotificacionAdmin.ENVIADO:
            return notification, True
        if (
            notification.estado == NotificacionAdmin.REINTENTANDO
            and notification.actualizado_en
            >= timezone.now() - timedelta(seconds=30)
        ):
            return notification, True
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

    try:
        email = EmailMessage(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [destinatario],
            reply_to=[reply_to] if reply_to else None,
        )
        sent_count = email.send(fail_silently=False)
        if sent_count != 1:
            raise smtplib.SMTPException("El servidor de correo no confirmó el envío.")
    except (smtplib.SMTPException, OSError, socket.timeout) as exc:
        logger.exception("Failed to send order notification for order %s", pedido_id)
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

    return notification, False


class PedidoApprovedNotificationView(APIView):
    permission_classes = [EsServicioInterno]

    def post(self, request):
        serializer = PedidoApprovedSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        pedido_id = data["pedido_id"]
        admin_recipient = _admin_recipient()
        if not admin_recipient:
            return Response(
                {"detail": "El correo administrativo debe ser distinto del remitente SMTP."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        lines = "\n".join(
            (
                f"- {item['producto_nombre']} (producto #{item['producto_id']}): "
                f"{item['cantidad']} unidad(es), {item['ancho_cm']} × "
                f"{item['alto_cm']} cm, ${item['precio_total']:,.0f} COP"
            )
            for item in data["detalles"]
        )
        admin_notification, admin_duplicate = _send_order_email(
            evento_id=f"pedido:{pedido_id}:payment-approved",
            pedido_id=pedido_id,
            destinatario=admin_recipient,
            subject=f"Pago aprobado para pedido #{pedido_id} — ${data['total']:,.0f} COP",
            message=(
                "Se aprobó el pago simulado de un pedido.\n\n"
                f"Pedido ID: {pedido_id}\n"
                f"Cliente: {data['cliente_nombre']} ({data['cliente_email']})\n"
                f"Total: ${data['total']:,.0f} COP\n\n"
                f"Productos:\n{lines}\n\n"
                "El pago fue aprobado por el simulador; no se realizó un cobro real.\n"
            ),
        )
        customer_notification, customer_duplicate = _send_order_email(
            evento_id=f"pedido:{pedido_id}:payment-approved:customer",
            pedido_id=pedido_id,
            destinatario=data["cliente_email"],
            subject=f"Pago confirmado para tu pedido #{pedido_id}",
            message=(
                f"Hola, el pago simulado de tu pedido #{pedido_id} fue aprobado.\n\n"
                f"Total: ${data['total']:,.0f} COP\n\n"
                f"Productos:\n{lines}\n\n"
                "Esta es una confirmación del simulador; no se realizó un cobro real."
            ),
        )

        return Response(
            {
                "notif_id": admin_notification.pk,
                "pedido_id": admin_notification.pedido_id,
                "estado": admin_notification.estado,
                "admin_estado": admin_notification.estado,
                "cliente_estado": customer_notification.estado,
                "intentos": admin_notification.intentos,
                "duplicate": admin_duplicate and customer_duplicate,
            },
            status=status.HTTP_200_OK,
        )


class PedidoCreatedNotificationView(APIView):
    permission_classes = [EsServicioInterno]

    def post(self, request):
        serializer = PedidoCreatedSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        pedido_id = data["pedido_id"]
        total = data["total"]
        lines = "\n".join(
            (
                f"- {item['producto_nombre']} (producto #{item['producto_id']}): "
                f"{item['cantidad']} unidad(es), "
                f"{item['ancho_cm']} × {item['alto_cm']} cm, "
                f"${item['precio_total']:,.0f} COP"
            )
            for item in data["detalles"]
        )
        customer_message = (
            f"Hola {data['cliente_nombre']}, recibimos tu pedido #{pedido_id}.\n\n"
            f"Total: ${total:,.0f} COP\n"
            f"Dirección de entrega: {data['direccion']}\n\n"
            f"Productos:\n{lines}\n\n"
            "El pago todavía está pendiente de confirmación en el simulador. "
            "No se realizó ningún cobro real."
        )
        customer_notification, customer_duplicate = _send_order_email(
            evento_id=f"pedido:{pedido_id}:order-created:customer",
            pedido_id=pedido_id,
            destinatario=data["cliente_email"],
            subject=f"Recibimos tu pedido #{pedido_id}",
            message=customer_message,
        )

        return Response(
            {
                "pedido_id": pedido_id,
                "admin_estado": "omitido",
                "cliente_estado": customer_notification.estado,
                "duplicate": customer_duplicate,
            },
            status=status.HTTP_200_OK,
        )


class PedidoStatusChangedNotificationView(APIView):
    permission_classes = [EsServicioInterno]

    def post(self, request):
        serializer = PedidoStatusChangedSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        pedido_id = data["pedido_id"]
        if not data["cliente_email"]:
            logger.error(
                "Order %s status notification has no customer email.",
                pedido_id,
            )
            return Response(
                {"detail": "El correo del cliente no está disponible."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        notification, duplicate = _send_order_email(
            evento_id=(
                f"pedido:{pedido_id}:status:{data['historial_id']}:customer"
            ),
            pedido_id=pedido_id,
            destinatario=data["cliente_email"],
            subject=f"Actualización de tu pedido #{pedido_id}: {data['estado_nuevo']}",
            message=(
                f"Hola {data['cliente_nombre']},\n\n"
                f"El estado de tu pedido #{pedido_id} ha cambiado.\n"
                f"Estado anterior: {data['estado_anterior']}\n"
                f"Estado nuevo: {data['estado_nuevo']}\n\n"
                "Gracias por tu compra."
            ),
        )
        return Response(
            {
                "pedido_id": pedido_id,
                "estado": notification.estado,
                "duplicate": duplicate,
            },
            status=status.HTTP_200_OK,
        )


class ContactMessageNotificationView(APIView):
    permission_classes = [EsServicioInterno]

    def post(self, request):
        serializer = ContactMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        admin_recipient = _admin_recipient()
        if not admin_recipient:
            return Response(
                {"detail": "El correo administrativo debe ser distinto del remitente SMTP."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        subject = "Nuevo mensaje desde el formulario de contacto"
        message = (
            "Recibiste un mensaje desde la sección Contacto.\n\n"
            f"Nombre: {data['nombre']}\n"
            f"Correo: {data['email']}\n"
            f"Asunto: {data.get('asunto') or '(sin asunto)'}\n\n"
            f"Mensaje:\n{data['mensaje']}\n"
        )
        try:
            email = EmailMessage(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [admin_recipient],
                reply_to=[data["email"]],
            )
            sent_count = email.send(fail_silently=False)
            if sent_count != 1:
                raise smtplib.SMTPException(
                    "El servidor de correo no confirmó el envío."
                )
        except (smtplib.SMTPException, OSError, socket.timeout):
            logger.exception("Failed to send a contact form message")
            return Response(
                {"detail": "No fue posible enviar el mensaje. Inténtalo de nuevo."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response({"estado": "enviado"}, status=status.HTTP_200_OK)
