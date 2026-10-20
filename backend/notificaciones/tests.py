import json
import tempfile
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import requests
from django.core.management import call_command
from django.test import SimpleTestCase, override_settings

from notificaciones.models import NotificacionAdmin
from notificaciones.utils import notificar_admin


@override_settings(
    NOTIFICATION_SERVICE_URL="http://notifications.test",
    NOTIFICATION_SERVICE_TIMEOUT_SECONDS=4,
    INTERNAL_SERVICE_TOKEN="test-internal-token",
)
class NotificationBridgeTests(SimpleTestCase):
    def setUp(self):
        self.order = SimpleNamespace(
            pedido_id=32,
            total="900.00",
            cliente=SimpleNamespace(
                usuario=SimpleNamespace(
                    nombre="Cliente de prueba",
                    email="customer@example.com",
                )
            ),
            direccion=SimpleNamespace(
                nombre_recibe="Persona receptora",
                calle="Calle 10",
                numero="20",
                barrio="Centro",
                ciudad=SimpleNamespace(
                    nombre="Bogotá",
                    departamento=SimpleNamespace(nombre="Cundinamarca"),
                ),
                complemento="Apto 301",
            ),
            detalles=SimpleNamespace(
                all=lambda: [
                    SimpleNamespace(
                        producto=7,
                        cantidad=2,
                        ancho_cm="100.00",
                        alto_cm="200.00",
                        precio_total="900.00",
                    )
                ]
            ),
        )

    @patch("notificaciones.utils.requests.post")
    @patch(
        "notificaciones.utils.Producto.objects.in_bulk",
        return_value={7: SimpleNamespace(nombre="Cortina Blackout")},
    )
    def test_payment_notification_is_forwarded_with_complete_order_details(
        self,
        products,
        post,
    ):
        post.return_value.json.return_value = {
            "pedido_id": 32,
            "estado": NotificacionAdmin.ENVIADO,
        }

        result = notificar_admin(self.order)

        self.assertEqual(result["estado"], NotificacionAdmin.ENVIADO)
        post.assert_called_once_with(
            "http://notifications.test/api/internal/notificaciones/pedidos/",
            json={
                "pedido_id": 32,
                "cliente_nombre": "Cliente de prueba",
                "cliente_email": "customer@example.com",
                "nombre_recibe": "Persona receptora",
                "direccion": "Calle 10 20, Centro, Bogotá, Cundinamarca, Apto 301",
                "total": "900.00",
                "detalles": [
                    {
                        "producto_id": 7,
                        "producto_nombre": "Cortina Blackout",
                        "cantidad": 2,
                        "ancho_cm": "100.00",
                        "alto_cm": "200.00",
                        "precio_total": "900.00",
                    }
                ],
            },
            headers={"X-Internal-Service-Token": "test-internal-token"},
            timeout=4,
        )
        products.assert_called_once_with({7}, field_name="producto_id")

    @patch("notificaciones.utils.NotificacionAdmin.objects.create")
    @patch("notificaciones.utils.requests.post")
    def test_service_unavailable_records_legacy_failure_and_returns(
        self,
        post,
        create,
    ):
        post.side_effect = requests.ConnectionError("unavailable")
        self.order.detalles = SimpleNamespace(all=lambda: [])

        result = notificar_admin(self.order)

        self.assertEqual(result["estado"], NotificacionAdmin.FALLIDO)
        create.assert_called_once()
        kwargs = create.call_args.kwargs
        self.assertIs(kwargs["pedido"], self.order)
        self.assertEqual(kwargs["estado"], NotificacionAdmin.FALLIDO)
        self.assertIn("unavailable", kwargs["error_detalle"])

    @patch(
        "notificaciones.management.commands.export_notification_history."
        "NotificacionAdmin.objects.order_by"
    )
    def test_history_export_writes_only_to_external_path(self, order_by):
        order_by.return_value.values.return_value = [
            {
                "notif_id": 7,
                "pedido_id": 32,
                "destinatario": "admin@example.com",
                "estado": "fallido",
                "fecha_envio": datetime(2024, 1, 1, tzinfo=timezone.utc),
                "intentos": 2,
                "error_detalle": "SMTP error",
            }
        ]
        with tempfile.TemporaryDirectory() as temp_dir:
            destination = Path(temp_dir) / "notifications.json"
            call_command(
                "export_notification_history",
                "--file",
                destination,
                stdout=StringIO(),
            )
            exported = json.loads(destination.read_text(encoding="utf-8"))

        self.assertEqual(exported["notificaciones"][0]["notif_id"], 7)
        self.assertEqual(exported["notificaciones"][0]["pedido_id"], 32)
