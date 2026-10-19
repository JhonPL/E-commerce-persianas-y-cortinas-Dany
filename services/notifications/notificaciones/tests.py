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


@override_settings(INTERNAL_SERVICE_TOKEN="test-internal-token")
class NotificationApiTests(APITestCase):
    def setUp(self):
        self.payload = {
            "pedido_id": 41,
            "cliente_email": "customer@example.com",
            "total": "125000.00",
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

    def test_approved_order_sends_email_and_records_delivery(self):
        response = self._post()
        notification = NotificacionAdmin.objects.get()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["estado"], NotificacionAdmin.ENVIADO)
        self.assertEqual(notification.pedido_id, 41)
        self.assertEqual(notification.destinatario, "admin@tutienda.com")
        self.assertEqual(notification.intentos, 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Pedido ID: 41", mail.outbox[0].body)
        self.assertIn("Cliente: customer@example.com", mail.outbox[0].body)

    def test_retry_after_success_is_idempotent(self):
        first = self._post()
        second = self._post()

        self.assertEqual(first.data["estado"], NotificacionAdmin.ENVIADO)
        self.assertTrue(second.data["duplicate"])
        self.assertEqual(NotificacionAdmin.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 1)

    def test_concurrent_retry_does_not_start_a_second_email(self):
        NotificacionAdmin.objects.create(
            pedido_id=41,
            evento_id="pedido:41:payment-approved",
            destinatario="admin@tutienda.com",
            estado=NotificacionAdmin.REINTENTANDO,
            intentos=2,
        )

        response = self._post()

        self.assertTrue(response.data["duplicate"])
        self.assertEqual(response.data["estado"], NotificacionAdmin.REINTENTANDO)
        self.assertEqual(len(mail.outbox), 0)

    def test_stale_retry_can_be_reclaimed_after_worker_failure(self):
        notification = NotificacionAdmin.objects.create(
            pedido_id=41,
            evento_id="pedido:41:payment-approved",
            destinatario="admin@tutienda.com",
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
        self.assertEqual(len(mail.outbox), 1)

    @patch("notificaciones.views.send_mail", side_effect=OSError("SMTP unavailable"))
    def test_failed_delivery_is_recorded_and_can_be_retried(self, send_mail):
        failed = self._post()
        notification = NotificacionAdmin.objects.get()
        self.assertEqual(failed.status_code, status.HTTP_200_OK)
        self.assertEqual(failed.data["estado"], NotificacionAdmin.FALLIDO)
        self.assertEqual(notification.error_detalle, "SMTP unavailable")

        send_mail.side_effect = None
        send_mail.return_value = 1
        retried = self._post()
        notification.refresh_from_db()
        self.assertEqual(retried.data["estado"], NotificacionAdmin.ENVIADO)
        self.assertEqual(notification.intentos, 2)
        self.assertIsNone(notification.error_detalle)


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
