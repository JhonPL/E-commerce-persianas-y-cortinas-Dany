import base64
import json
import tempfile
from datetime import datetime, timedelta, timezone
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.core import mail
from django.test import override_settings
from django.utils import timezone as django_timezone
from rest_framework import status
from rest_framework.test import APITestCase

from .models import NotificacionAdmin
from notification_service.local_config import (
    apply_local_settings,
    load_local_settings,
)


class LocalNotificationSettingsTests(APITestCase):
    def test_loads_local_settings_without_exposing_them(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = (
                Path(temp_dir)
                / "CortinasPersianas"
                / "config"
                / "notifications.json"
            )
            config_path.parent.mkdir(parents=True)
            config_path.write_text(
                json.dumps({
                    "EMAIL_HOST_PASSWORD": "test-app-password",
                    "EMAIL_HOST_USER": "sender@example.test",
                }),
                encoding="utf-8",
            )

            config = load_local_settings(temp_dir)

        self.assertEqual(
            config,
            {
                "EMAIL_HOST_PASSWORD": "test-app-password",
                "EMAIL_HOST_USER": "sender@example.test",
            },
        )

    def test_missing_local_settings_are_optional(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            self.assertEqual(load_local_settings(temp_dir), {})

    def test_local_settings_fill_empty_values_but_preserve_environment(self):
        environment = {
            "EMAIL_HOST_PASSWORD": "",
            "EMAIL_HOST_USER": "environment@example.test",
        }

        apply_local_settings(
            {
                "EMAIL_HOST_PASSWORD": "test-app-password",
                "EMAIL_HOST_USER": "local@example.test",
            },
            environment,
        )

        self.assertEqual(environment["EMAIL_HOST_PASSWORD"], "test-app-password")
        self.assertEqual(
            environment["EMAIL_HOST_USER"],
            "environment@example.test",
        )

    def test_invalid_local_settings_raise_a_clear_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = (
                Path(temp_dir)
                / "CortinasPersianas"
                / "config"
                / "notifications.json"
            )
            config_path.parent.mkdir(parents=True)
            config_path.write_text("{invalid", encoding="utf-8")

            with self.assertRaisesMessage(
                RuntimeError,
                "No se pudo leer la configuración local de notificaciones.",
            ):
                load_local_settings(temp_dir)


@override_settings(
    INTERNAL_SERVICE_TOKEN="test-internal-token",
    ADMIN_EMAIL="jhonpaternina2002@gmail.com",
    DEFAULT_FROM_EMAIL="jhon.paternina302@gmail.com",
)
class NotificationApiTests(APITestCase):
    def setUp(self):
        self.payload = {
            "pedido_id": 41,
            "cliente_nombre": "Cliente de prueba",
            "cliente_email": "customer@example.com",
            "nombre_recibe": "Persona receptora",
            "direccion": "Calle 10, Granada, Meta",
            "total": "125000.00",
            "numero_factura": "DEMO-000041",
            "pdf_base64": base64.b64encode(b"%PDF-1.4 demo").decode("ascii"),
            "detalles": [
                {
                    "producto_id": 12,
                    "producto_nombre": "Cortina Blackout",
                    "cantidad": 1,
                    "ancho_cm": "100.00",
                    "alto_cm": "200.00",
                    "precio_total": "125000.00",
                }
            ],
        }

    def _post(self):
        return self.client.post(
            "/api/internal/notificaciones/pedidos/",
            self.payload,
            format="json",
            HTTP_X_INTERNAL_SERVICE_TOKEN="test-internal-token",
        )

    def test_notification_requires_internal_token(self):
        response = self.client.post(
            "/api/internal/notificaciones/pedidos/",
            self.payload,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(NotificacionAdmin.objects.count(), 0)

    @override_settings(ADMIN_EMAIL="jhon.paternina302@gmail.com")
    def test_payment_notice_rejects_sender_as_admin_recipient(self):
        response = self._post()

        self.assertEqual(
            response.status_code,
            status.HTTP_503_SERVICE_UNAVAILABLE,
        )
        self.assertEqual(NotificacionAdmin.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_approved_order_sends_email_and_records_delivery(self):
        response = self._post()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["estado"], NotificacionAdmin.ENVIADO)
        self.assertEqual(response.data["admin_estado"], NotificacionAdmin.ENVIADO)
        self.assertEqual(response.data["cliente_estado"], NotificacionAdmin.ENVIADO)
        self.assertEqual(NotificacionAdmin.objects.count(), 2)
        admin_notification = NotificacionAdmin.objects.get(
            evento_id="pedido:41:payment-approved",
        )
        customer_notification = NotificacionAdmin.objects.get(
            evento_id="pedido:41:payment-approved:customer",
        )
        self.assertEqual(admin_notification.pedido_id, 41)
        self.assertEqual(
            admin_notification.destinatario,
            "jhonpaternina2002@gmail.com",
        )
        self.assertEqual(admin_notification.intentos, 1)
        self.assertEqual(
            customer_notification.destinatario,
            "customer@example.com",
        )
        self.assertEqual(len(mail.outbox), 2)
        admin_message = next(
            message
            for message in mail.outbox
            if message.to == ["jhonpaternina2002@gmail.com"]
        )
        customer_message = next(
            message
            for message in mail.outbox
            if message.to == ["customer@example.com"]
        )
        self.assertEqual(admin_message.from_email, "jhon.paternina302@gmail.com")
        self.assertEqual(customer_message.from_email, "jhon.paternina302@gmail.com")
        self.assertIn("Pedido ID: 41", admin_message.body)
        self.assertIn("customer@example.com", admin_message.body)
        self.assertIn("Cortina Blackout", admin_message.body)
        self.assertIn("Productos:", admin_message.body)
        self.assertIn("Nuevo pedido recibido", admin_message.subject)
        self.assertIn("Pago confirmado", customer_message.subject)
        self.assertIn("¡Pago confirmado!", customer_message.alternatives[0][0])
        self.assertIn("Cliente de prueba", customer_message.alternatives[0][0])
        self.assertIn("Cortina Blackout", customer_message.alternatives[0][0])
        self.assertIn("Persona receptora", customer_message.alternatives[0][0])
        self.assertIn("Calle 10", customer_message.alternatives[0][0])
        self.assertIn("Abrir gestión de pedidos", admin_message.alternatives[0][0])
        self.assertIn("cid:brand-logo", customer_message.alternatives[0][0])
        pdf_attachments = [
            attachment
            for attachment in customer_message.attachments
            if isinstance(attachment, tuple)
            and attachment[2] == "application/pdf"
        ]
        self.assertEqual(len(pdf_attachments), 1)
        self.assertEqual(pdf_attachments[0][0], "DEMO-000041.pdf")
        self.assertEqual(pdf_attachments[0][1], b"%PDF-1.4 demo")
        self.assertIn(
            b"Content-ID: <brand-logo>",
            customer_message.message().as_bytes(),
        )
        self.assertIn(
            b"Content-Type: image/png",
            customer_message.message().as_bytes(),
        )

    def test_approved_order_rejects_non_pdf_attachment(self):
        self.payload["pdf_base64"] = base64.b64encode(b"not a pdf").decode("ascii")

        response = self._post()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(NotificacionAdmin.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_same_admin_and_customer_recipient_gets_separate_emails(self):
        self.payload["cliente_email"] = "jhonpaternina2002@gmail.com"

        first = self._post()
        retry = self._post()

        self.assertEqual(first.status_code, status.HTTP_200_OK)
        self.assertEqual(first.data["admin_estado"], NotificacionAdmin.ENVIADO)
        self.assertEqual(first.data["cliente_estado"], NotificacionAdmin.ENVIADO)
        self.assertEqual(retry.status_code, status.HTTP_200_OK)
        self.assertTrue(retry.data["duplicate"])
        self.assertEqual(NotificacionAdmin.objects.count(), 2)
        self.assertEqual(len(mail.outbox), 2)
        admin_message = next(
            message for message in mail.outbox
            if "Nuevo pedido recibido" in message.subject
        )
        customer_message = next(
            message for message in mail.outbox
            if "Pago confirmado" in message.subject
        )
        self.assertEqual(admin_message.to, ["jhonpaternina2002@gmail.com"])
        self.assertEqual(customer_message.to, ["jhonpaternina2002@gmail.com"])
        pdf_attachments = [
            attachment
            for attachment in customer_message.attachments
            if isinstance(attachment, tuple)
            and attachment[2] == "application/pdf"
        ]
        self.assertEqual(len(pdf_attachments), 1)
        self.assertEqual(pdf_attachments[0][0], "DEMO-000041.pdf")
        admin_pdf_attachments = [
            attachment
            for attachment in admin_message.attachments
            if isinstance(attachment, tuple)
            and attachment[2] == "application/pdf"
        ]
        self.assertEqual(len(admin_pdf_attachments), 1)
        self.assertEqual(admin_pdf_attachments[0][0], "DEMO-000041.pdf")
        self.assertEqual(admin_pdf_attachments[0][1], b"%PDF-1.4 demo")

    def test_retry_after_success_is_idempotent(self):
        first = self._post()
        second = self._post()

        self.assertEqual(first.data["estado"], NotificacionAdmin.ENVIADO)
        self.assertTrue(second.data["duplicate"])
        self.assertEqual(NotificacionAdmin.objects.count(), 2)
        self.assertEqual(len(mail.outbox), 2)

    def test_concurrent_retry_does_not_start_a_second_email(self):
        NotificacionAdmin.objects.create(
            pedido_id=41,
            evento_id="pedido:41:payment-approved",
            destinatario="jhonpaternina2002@gmail.com",
            estado=NotificacionAdmin.REINTENTANDO,
            intentos=2,
        )

        response = self._post()

        self.assertFalse(response.data["duplicate"])
        self.assertEqual(response.data["admin_estado"], NotificacionAdmin.REINTENTANDO)
        self.assertEqual(response.data["cliente_estado"], NotificacionAdmin.ENVIADO)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["customer@example.com"])

    def test_stale_retry_can_be_reclaimed_after_worker_failure(self):
        notification = NotificacionAdmin.objects.create(
            pedido_id=41,
            evento_id="pedido:41:payment-approved",
            destinatario="jhonpaternina2002@gmail.com",
            estado=NotificacionAdmin.REINTENTANDO,
            intentos=1,
        )
        NotificacionAdmin.objects.filter(pk=notification.pk).update(
            actualizado_en=django_timezone.now() - timedelta(seconds=31)
        )

        response = self._post()
        notification.refresh_from_db()

        self.assertEqual(response.data["estado"], NotificacionAdmin.ENVIADO)
        self.assertEqual(notification.intentos, 2)
        self.assertEqual(response.data["cliente_estado"], NotificacionAdmin.ENVIADO)
        self.assertEqual(len(mail.outbox), 2)

    @patch(
        "notificaciones.views.EmailMessage.send",
        side_effect=OSError("SMTP unavailable"),
    )
    def test_failed_delivery_is_recorded_and_can_be_retried(self, email_send):
        failed = self._post()
        notifications = NotificacionAdmin.objects.order_by("evento_id")
        self.assertEqual(failed.status_code, status.HTTP_200_OK)
        self.assertEqual(failed.data["estado"], NotificacionAdmin.FALLIDO)
        self.assertEqual(failed.data["cliente_estado"], NotificacionAdmin.FALLIDO)
        self.assertEqual(notifications.count(), 2)
        self.assertTrue(
            all(
                notification.error_detalle == "SMTP unavailable"
                for notification in notifications
            )
        )

        email_send.side_effect = None
        email_send.return_value = 1
        retried = self._post()
        notifications = list(NotificacionAdmin.objects.order_by("evento_id"))
        self.assertEqual(retried.data["estado"], NotificacionAdmin.ENVIADO)
        self.assertEqual(retried.data["cliente_estado"], NotificacionAdmin.ENVIADO)
        self.assertEqual(
            [notification.intentos for notification in notifications],
            [2, 2],
        )
        self.assertTrue(
            all(notification.error_detalle is None for notification in notifications)
        )


@override_settings(
    INTERNAL_SERVICE_TOKEN="test-internal-token",
    ADMIN_EMAIL="admin@example.com",
)
class ContactMessageNotificationTests(APITestCase):
    payload = {
        "nombre": "Cliente de prueba",
        "email": "customer@example.com",
        "asunto": "Consulta de cortinas",
        "mensaje": "Quisiera información sobre una cortina.",
    }

    def _post(self, payload=None, **headers):
        return self.client.post(
            "/api/internal/notificaciones/contacto/",
            payload or self.payload,
            format="json",
            **headers,
        )

    def test_contact_message_is_sent_to_admin_with_customer_reply_address(self):
        response = self._post(
            HTTP_X_INTERNAL_SERVICE_TOKEN="test-internal-token",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"estado": "enviado"})
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["admin@example.com"])
        self.assertEqual(mail.outbox[0].from_email, "jhon.paternina302@gmail.com")
        self.assertNotEqual(mail.outbox[0].from_email, mail.outbox[0].to[0])
        self.assertEqual(mail.outbox[0].reply_to, ["customer@example.com"])
        self.assertIn("Cliente de prueba", mail.outbox[0].body)
        self.assertIn("Consulta de cortinas", mail.outbox[0].body)
        self.assertIn("Quisiera información", mail.outbox[0].body)

    def test_contact_message_requires_internal_token(self):
        response = self._post()

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(len(mail.outbox), 0)

    def test_contact_message_reports_smtp_failure(self):
        with patch(
            "notificaciones.views.EmailMessage.send",
            side_effect=OSError("SMTP unavailable"),
        ):
            response = self._post(
                HTTP_X_INTERNAL_SERVICE_TOKEN="test-internal-token",
            )

        self.assertEqual(response.status_code, status.HTTP_502_BAD_GATEWAY)
        self.assertEqual(
            response.data["detail"],
            "No fue posible enviar el mensaje. Inténtalo de nuevo.",
        )

    @override_settings(
        ADMIN_EMAIL="jhon.paternina302@gmail.com",
        DEFAULT_FROM_EMAIL="jhon.paternina302@gmail.com",
        EMAIL_HOST_USER="jhon.paternina302@gmail.com",
    )
    def test_contact_message_never_sends_to_the_smtp_sender(self):
        response = self._post(
            HTTP_X_INTERNAL_SERVICE_TOKEN="test-internal-token",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_503_SERVICE_UNAVAILABLE,
        )
        self.assertEqual(len(mail.outbox), 0)


@override_settings(INTERNAL_SERVICE_TOKEN="test-internal-token")
class OrderStatusChangedNotificationTests(APITestCase):
    payload = {
        "pedido_id": 91,
        "historial_id": 104,
        "cliente_nombre": "Cliente de prueba",
        "cliente_email": "customer@example.com",
        "estado_anterior": "Pendiente de preparación",
        "estado_nuevo": "Preparado",
    }

    def _post(self, payload=None, **headers):
        return self.client.post(
            "/api/internal/notificaciones/pedidos/estado/",
            payload or self.payload,
            format="json",
            **headers,
        )

    def test_status_change_notifies_customer_once_per_transition(self):
        first = self._post(
            HTTP_X_INTERNAL_SERVICE_TOKEN="test-internal-token",
        )
        retry = self._post(
            HTTP_X_INTERNAL_SERVICE_TOKEN="test-internal-token",
        )

        self.assertEqual(first.status_code, status.HTTP_200_OK)
        self.assertEqual(first.data["estado"], NotificacionAdmin.ENVIADO)
        self.assertTrue(retry.data["duplicate"])
        notification = NotificacionAdmin.objects.get()
        self.assertEqual(notification.pedido_id, 91)
        self.assertEqual(notification.destinatario, "customer@example.com")
        self.assertEqual(notification.evento_id, "pedido:91:status:104:customer")
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["customer@example.com"])
        self.assertIn("Estado anterior: Pendiente de preparación", mail.outbox[0].body)
        self.assertIn("Estado nuevo: Preparado", mail.outbox[0].body)
        status_html = mail.outbox[0].alternatives[0][0]
        self.assertIn("Tu pedido está en preparación", status_html)
        self.assertIn("En preparación", status_html)
        self.assertIn("cid:brand-logo", status_html)

    def test_sent_order_uses_on_the_way_email_case(self):
        payload = {**self.payload, "estado_nuevo": "Enviado"}
        response = self._post(
            payload,
            HTTP_X_INTERNAL_SERVICE_TOKEN="test-internal-token",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        html = mail.outbox[0].alternatives[0][0]
        self.assertIn("Tu pedido está en camino", html)
        self.assertIn("En camino", html)
        self.assertIn("transportadora o número de guía", html)

    def test_status_change_notification_requires_internal_token(self):
        response = self._post()

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(NotificacionAdmin.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)

    @patch(
        "notificaciones.views.EmailMessage.send",
        side_effect=OSError("SMTP unavailable"),
    )
    def test_status_change_smtp_failure_is_recorded(self, email_send):
        response = self._post(
            HTTP_X_INTERNAL_SERVICE_TOKEN="test-internal-token",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["estado"], NotificacionAdmin.FALLIDO)
        self.assertEqual(
            NotificacionAdmin.objects.get().error_detalle,
            "SMTP unavailable",
        )
        email_send.assert_called_once()


class NotificationHistoryImportTests(APITestCase):
    def test_import_preserves_ids_order_reference_and_timestamp(self):
        timestamp = datetime(2024, 1, 2, 3, 4, tzinfo=timezone.utc).isoformat()
        payload = {
            "notificaciones": [
                {
                    "notif_id": 17,
                    "pedido_id": 25,
                    "destinatario": "admin@example.com",
                    "estado": NotificacionAdmin.FALLIDO,
                    "fecha_envio": timestamp,
                    "intentos": 3,
                    "error_detalle": "SMTP error",
                }
            ]
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            transfer = Path(temp_dir) / "notifications.json"
            transfer.write_text(json.dumps(payload), encoding="utf-8")
            call_command(
                "import_notification_history",
                transfer,
                stdout=StringIO(),
            )

        notification = NotificacionAdmin.objects.get(pk=17)
        self.assertEqual(notification.pedido_id, 25)
        self.assertEqual(notification.intentos, 3)
        self.assertEqual(notification.estado, NotificacionAdmin.FALLIDO)
        self.assertEqual(notification.fecha_envio.isoformat(), timestamp)

    def test_import_rejects_nonempty_database(self):
        NotificacionAdmin.objects.create(
            pedido_id=25,
            destinatario="admin@example.com",
        )
        payload = {"notificaciones": []}
        with tempfile.TemporaryDirectory() as temp_dir:
            transfer = Path(temp_dir) / "notifications.json"
            transfer.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesMessage(
                CommandError,
                "La base de notificaciones no está vacía; se canceló la importación.",
            ):
                call_command("import_notification_history", transfer)
