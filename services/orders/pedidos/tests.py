from decimal import Decimal
from datetime import timedelta
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

import requests
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APIClient, APITestCase

from .authentication import RemoteUser
from .models import (
    Ciudad,
    Departamento,
    DetallePedido,
    Direccion,
    EstadoPedido,
    HistorialEstadoPedido,
    Pedido,
)


@override_settings(
    INTERNAL_SERVICE_TOKEN="internal-test-token",
    AUTH_SERVICE_URL="http://identity.test/api/v1/auth/me/",
    CATALOGO_SERVICE_INTERNAL_URL="http://catalog.test/api/internal/catalogo",
    NOTIFICATIONS_SERVICE_URL="http://notifications.test",
)
class OrdersServiceTests(APITestCase):
    def setUp(self):
        self.department = Departamento.objects.create(
            nombre="Cundinamarca",
        )
        self.city = Ciudad.objects.create(
            nombre="Bogota",
            departamento=self.department,
        )
        self.address = Direccion.objects.create(
            usuario=17,
            ciudad=self.city,
            calle="Calle 10",
            numero="20",
            barrio="Centro",
        )
        self.pending = EstadoPedido.objects.create(
            nombre=EstadoPedido.PENDIENTE,
        )
        self.order = Pedido.objects.create(
            usuario=17,
            cliente_nombre="Cliente Demo",
            cliente_email="cliente@example.test",
            direccion=self.address,
            estado=self.pending,
            total="480000.00",
        )
        DetallePedido.objects.create(
            pedido=self.order,
            producto=21,
            cantidad=2,
            ancho_cm="100.00",
            alto_cm="200.00",
            area_m2="2.0000",
            precio_m2="120000.00",
            precio_total="480000.00",
        )

    @patch("pedidos.catalog.requests.get")
    def test_customer_can_only_read_their_own_orders(self, catalog_get):
        catalog_get.return_value = Mock(
            raise_for_status=Mock(),
            json=lambda: [
                {
                    "producto_id": 21,
                    "nombre": "Blackout",
                    "imagen_principal": "https://images.test/blackout.jpg",
                }
            ],
        )
        self.client.force_authenticate(user=RemoteUser(17, "cliente"))

        response = self.client.get("/api/v1/pedidos/")
        denied = self.client.get(f"/api/v1/pedidos/{self.order.pk + 1}/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total"], 1)
        self.assertEqual(response.data["pedidos"][0]["cliente_nombre"], "Cliente Demo")
        self.assertEqual(response.data["pedidos"][0]["detalles"][0]["nombre"], "Blackout")
        self.assertEqual(denied.status_code, 404)

    @patch("pedidos.views.requests.post")
    def test_admin_can_filter_orders_and_change_status(self, notification_post):
        admin_client = APIClient()
        admin_client.force_authenticate(user=RemoteUser(4, "admin"))
        prepared = EstadoPedido.objects.create(nombre=EstadoPedido.PREPARADO)
        notification_post.return_value = Mock(
            raise_for_status=Mock(),
            json=lambda: {
                "pedido_id": self.order.pedido_id,
                "estado": "enviado",
            },
        )

        listing = admin_client.get(
            "/api/v1/admin/pedidos/",
            {"search": "cliente@example.test"},
        )
        changed = admin_client.patch(
            f"/api/v1/admin/pedidos/{self.order.pk}/estado/",
            {"estado_id": prepared.pk},
            format="json",
        )

        self.assertEqual(listing.status_code, 200)
        self.assertEqual(listing.data["total"], 1)
        self.assertEqual(changed.status_code, 200)
        self.assertEqual(changed.data["notificacion_estado"], "enviado")
        self.order.refresh_from_db()
        self.assertEqual(self.order.estado_id, prepared.pk)
        notification_post.assert_called_once()
        notification_payload = notification_post.call_args.kwargs["json"]
        self.assertEqual(notification_payload["pedido_id"], self.order.pedido_id)
        self.assertEqual(notification_payload["cliente_email"], self.order.cliente_email)
        self.assertEqual(
            notification_payload["estado_anterior"],
            EstadoPedido.PENDIENTE,
        )
        self.assertEqual(
            notification_payload["estado_nuevo"],
            EstadoPedido.PREPARADO,
        )
        self.assertTrue(
            HistorialEstadoPedido.objects.filter(
                historial_id=notification_payload["historial_id"],
                pedido=self.order,
            ).exists()
        )
        self.assertTrue(
            HistorialEstadoPedido.objects.filter(
                pedido=self.order,
                cambiado_por=4,
            ).exists()
        )

    def test_admin_only_sees_paid_orders_and_fulfillment_states(self):
        admin_client = APIClient()
        admin_client.force_authenticate(user=RemoteUser(4, "admin"))
        payment_pending = EstadoPedido.objects.create(nombre="Pendiente de pago")
        payment_declined = EstadoPedido.objects.create(nombre="Pago rechazado")
        unpaid_orders = [
            Pedido.objects.create(
                usuario=17,
                cliente_nombre="Cliente Demo",
                cliente_email="cliente@example.test",
                direccion=self.address,
                estado=state,
                total="100000.00",
            )
            for state in (payment_pending, payment_declined)
        ]

        listing = admin_client.get("/api/v1/admin/pedidos/")
        states = admin_client.get("/api/v1/admin/estados-pedido/")

        self.assertEqual(listing.status_code, 200)
        self.assertEqual(listing.data["total"], 1)
        self.assertEqual(
            [order["pedido_id"] for order in listing.data["pedidos"]],
            [self.order.pedido_id],
        )
        self.assertEqual(states.status_code, 200)
        self.assertEqual(
            {state["nombre"] for state in states.data},
            {
                EstadoPedido.PENDIENTE,
                EstadoPedido.PREPARADO,
                EstadoPedido.ENVIADO,
            },
        )
        self.assertTrue(
            all(
                order.estado_id in (payment_pending.pk, payment_declined.pk)
                for order in unpaid_orders
            )
        )

    def test_admin_cannot_manage_payment_state_or_unpaid_order(self):
        admin_client = APIClient()
        admin_client.force_authenticate(user=RemoteUser(4, "admin"))
        payment_pending = EstadoPedido.objects.create(nombre="Pendiente de pago")
        payment_declined = EstadoPedido.objects.create(nombre="Pago rechazado")
        awaiting_payment = Pedido.objects.create(
            usuario=17,
            cliente_nombre="Cliente Demo",
            cliente_email="cliente@example.test",
            direccion=self.address,
            estado=payment_pending,
            total="100000.00",
        )
        prepared = EstadoPedido.objects.create(nombre=EstadoPedido.PREPARADO)
        sent = EstadoPedido.objects.create(nombre=EstadoPedido.ENVIADO)

        change_to_declined = admin_client.patch(
            f"/api/v1/admin/pedidos/{self.order.pk}/estado/",
            {"estado_id": payment_declined.pk},
            format="json",
        )
        change_to_pending = admin_client.patch(
            f"/api/v1/admin/pedidos/{self.order.pk}/estado/",
            {"estado_id": self.pending.pk},
            format="json",
        )
        skip_to_sent = admin_client.patch(
            f"/api/v1/admin/pedidos/{self.order.pk}/estado/",
            {"estado_id": sent.pk},
            format="json",
        )
        fulfill_unpaid = admin_client.patch(
            f"/api/v1/admin/pedidos/{awaiting_payment.pk}/estado/",
            {"estado_id": prepared.pk},
            format="json",
        )

        self.assertEqual(change_to_declined.status_code, 400)
        self.assertEqual(change_to_pending.status_code, 400)
        self.assertEqual(skip_to_sent.status_code, 400)
        self.assertEqual(fulfill_unpaid.status_code, 400)
        self.order.refresh_from_db()
        awaiting_payment.refresh_from_db()
        self.assertEqual(self.order.estado.nombre, EstadoPedido.PENDIENTE)
        self.assertEqual(awaiting_payment.estado_id, payment_pending.pk)
        self.assertFalse(
            HistorialEstadoPedido.objects.filter(pedido=awaiting_payment).exists()
        )

    @patch("pedidos.views.requests.post")
    def test_admin_can_advance_prepared_order_to_sent(self, notification_post):
        admin_client = APIClient()
        admin_client.force_authenticate(user=RemoteUser(4, "admin"))
        prepared = EstadoPedido.objects.create(nombre=EstadoPedido.PREPARADO)
        sent = EstadoPedido.objects.create(nombre=EstadoPedido.ENVIADO)
        self.order.estado = prepared
        self.order.save(update_fields=["estado"])
        notification_post.return_value = Mock(
            raise_for_status=Mock(),
            json=lambda: {
                "pedido_id": self.order.pedido_id,
                "estado": "enviado",
            },
        )

        changed = admin_client.patch(
            f"/api/v1/admin/pedidos/{self.order.pk}/estado/",
            {"estado_id": sent.pk},
            format="json",
        )

        self.assertEqual(changed.status_code, 200)
        self.assertEqual(changed.data["notificacion_estado"], "enviado")
        self.order.refresh_from_db()
        self.assertEqual(self.order.estado_id, sent.pk)
        notification_post.assert_called_once()

    @patch(
        "pedidos.views.requests.post",
        side_effect=requests.ConnectionError("notifications unavailable"),
    )
    def test_admin_state_change_is_kept_when_notification_service_is_unavailable(
        self,
        notification_post,
    ):
        admin_client = APIClient()
        admin_client.force_authenticate(user=RemoteUser(4, "admin"))
        prepared = EstadoPedido.objects.create(nombre=EstadoPedido.PREPARADO)

        changed = admin_client.patch(
            f"/api/v1/admin/pedidos/{self.order.pk}/estado/",
            {"estado_id": prepared.pk},
            format="json",
        )

        self.assertEqual(changed.status_code, 200)
        self.assertEqual(changed.data["notificacion_estado"], "fallido")
        self.order.refresh_from_db()
        self.assertEqual(self.order.estado_id, prepared.pk)
        notification_post.assert_called_once()

    def test_internal_product_reference_check_is_service_authenticated(self):
        internal_client = APIClient()

        denied = internal_client.get(
            "/api/internal/pedidos/productos/21/",
            HTTP_X_INTERNAL_SERVICE_TOKEN="wrong-token",
        )
        referenced = internal_client.get(
            "/api/internal/pedidos/productos/21/",
            HTTP_X_INTERNAL_SERVICE_TOKEN="internal-test-token",
        )
        not_referenced = internal_client.get(
            "/api/internal/pedidos/productos/22/",
            HTTP_X_INTERNAL_SERVICE_TOKEN="internal-test-token",
        )

        self.assertEqual(denied.status_code, 401)
        self.assertEqual(referenced.status_code, 409)
        self.assertEqual(not_referenced.status_code, 200)


class ImportOrdersCommandTests(APITestCase):
    def test_import_preserves_ids_and_rejects_nonempty_database(self):
        payload = {
            "schema_version": 1,
            "departamentos": [{"departamento_id": 8, "nombre": "Cundinamarca"}],
            "ciudades": [
                {
                    "ciudad_id": 9,
                    "nombre": "Bogota",
                    "departamento_id": 8,
                }
            ],
            "direcciones": [
                {
                    "direccion_id": 10,
                    "usuario_id": 17,
                    "ciudad_id": 9,
                    "barrio": "Centro",
                    "calle": "Calle 10",
                    "numero": "20",
                    "complemento": "",
                    "es_principal": True,
                }
            ],
            "estados": [
                {"estado_id": 11, "nombre": EstadoPedido.PENDIENTE}
            ],
            "pedidos": [
                {
                    "pedido_id": 12,
                    "usuario_id": 17,
                    "cliente_nombre": "Cliente Demo",
                    "cliente_email": "cliente@example.test",
                    "direccion_id": 10,
                    "estado_id": 11,
                    "fecha_pedido": "2026-10-01T12:00:00+00:00",
                    "total": "480000.00",
                    "referencia_pago": "",
                    "notas": "Migrado",
                }
            ],
            "detalles": [
                {
                    "detalle_id": 13,
                    "pedido_id": 12,
                    "producto_id": 21,
                    "cantidad": 1,
                    "ancho_cm": "100.00",
                    "alto_cm": "200.00",
                    "area_m2": "2.0000",
                    "precio_m2": "240000.00",
                    "precio_total": "480000.00",
                }
            ],
            "historial": [
                {
                    "historial_id": 14,
                    "pedido_id": 12,
                    "estado_id": 11,
                    "cambiado_en": "2026-10-01T12:05:00+00:00",
                    "cambiado_por_id": 4,
                    "notas_cambio": "Estado inicial",
                }
            ],
        }
        with TemporaryDirectory() as directory:
            fixture = Path(directory) / "orders.json"
            fixture.write_text(json.dumps(payload), encoding="utf-8")

            call_command("import_orders", input=str(fixture))

            migrated = Pedido.objects.get(pk=12)
            self.assertEqual(migrated.usuario, 17)
            self.assertEqual(migrated.cliente_email, "cliente@example.test")
            self.assertEqual(migrated.fecha_pedido.year, 2026)
            self.assertTrue(
                DetallePedido.objects.filter(
                    detalle_id=13,
                    pedido_id=12,
                    producto=21,
                ).exists()
            )
            self.assertTrue(
                HistorialEstadoPedido.objects.filter(
                    historial_id=14,
                    cambiado_por=4,
                ).exists()
            )
            with self.assertRaises(CommandError):
                call_command("import_orders", input=str(fixture))


@override_settings(
    INTERNAL_SERVICE_TOKEN="internal-test-token",
    CART_SERVICE_URL="http://cart.test/api/v1/carrito",
    SERVICE_TIMEOUT_SECONDS=2,
)
class CheckoutTests(APITestCase):
    def setUp(self):
        self.client.force_authenticate(
            user=RemoteUser(
                17,
                "cliente",
                nombre="Cliente demo",
                email="cliente@example.test",
            )
        )
        self.payload = {
            "direccion": {
                "departamento": "Cundinamarca",
                "ciudad": "Bogota",
                "barrio": "Centro",
                "calle": "Calle 10",
                "numero": "20",
            },
            "total": "0.01",
        }
        self.cart_item = {
            "producto_id": 21,
            "cantidad": 2,
            "ancho_cm": "100.00",
            "alto_cm": "200.00",
            "precio_m2": "120000.00",
        }

    @patch("pedidos.views.requests.post")
    @patch("pedidos.views.requests.get")
    @patch("pedidos.views.get_catalog_products")
    def test_checkout_uses_service_cart_prices_not_client_total(
        self,
        catalog_products,
        cart_get,
        notification_post,
    ):
        catalog_products.return_value = {
            21: {"nombre": "Cortina Blackout"},
        }
        cart_get.return_value = Mock(
            raise_for_status=Mock(),
            json=lambda: {"items": [self.cart_item]},
        )
        notification_post.return_value = Mock(
            raise_for_status=Mock(),
            json=lambda: {
                "pedido_id": Pedido.objects.latest("pedido_id").pedido_id,
                "admin_estado": "omitido",
                "cliente_estado": "enviado",
            },
        )

        response = self.client.post(
            "/api/v1/pedidos/checkout/",
            self.payload,
            format="json",
            HTTP_AUTHORIZATION="Bearer test-user-token",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["total"], "480000.00")
        self.assertEqual(response.data["notificacion"], "enviado")
        self.assertEqual(Pedido.objects.get().total, Decimal("480000.00"))
        self.assertEqual(
            DetallePedido.objects.get().precio_total,
            Decimal("480000.00"),
        )
        self.assertEqual(
            DetallePedido.objects.get().producto_nombre,
            "Cortina Blackout",
        )
        self.assertEqual(response.data["estado"], "Pendiente de pago")
        cart_get.assert_called_once()
        notification_post.assert_called_once()
        notification_payload = notification_post.call_args.kwargs["json"]
        self.assertEqual(notification_payload["cliente_email"], "cliente@example.test")
        self.assertEqual(notification_payload["detalles"][0]["producto_id"], 21)
        self.assertEqual(
            notification_payload["detalles"][0]["producto_nombre"],
            "Cortina Blackout",
        )
        self.assertEqual(
            notification_post.call_args.kwargs["headers"][
                "X-Internal-Service-Token"
            ],
            "internal-test-token",
        )

    @patch("pedidos.views.requests.get")
    def test_checkout_rejects_an_empty_cart(self, cart_get):
        cart_get.return_value = Mock(
            raise_for_status=Mock(),
            json=lambda: {"items": []},
        )

        response = self.client.post(
            "/api/v1/pedidos/checkout/",
            self.payload,
            format="json",
            HTTP_AUTHORIZATION="Bearer test-user-token",
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(Pedido.objects.exists())

    @patch(
        "pedidos.views.requests.post",
        side_effect=requests.ConnectionError("notifications unavailable"),
    )
    @patch("pedidos.views.requests.get")
    @patch("pedidos.views.get_catalog_products")
    def test_checkout_keeps_order_and_reports_notification_failure(
        self,
        catalog_products,
        cart_get,
        notification_post,
    ):
        catalog_products.return_value = {
            21: {"nombre": "Cortina Blackout"},
        }
        cart_get.return_value = Mock(
            raise_for_status=Mock(),
            json=lambda: {"items": [self.cart_item]},
        )

        response = self.client.post(
            "/api/v1/pedidos/checkout/",
            self.payload,
            format="json",
            HTTP_AUTHORIZATION="******",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["notificacion"], "fallido")
        self.assertEqual(
            Pedido.objects.filter(cliente_email="cliente@example.test").count(),
            1,
        )
        notification_post.assert_called_once()


@override_settings(INTERNAL_SERVICE_TOKEN="internal-test-token")
class InternalPaymentResultTests(APITestCase):
    def setUp(self):
        department = Departamento.objects.create(nombre="Cundinamarca")
        city = Ciudad.objects.create(nombre="Bogota", departamento=department)
        address = Direccion.objects.create(
            usuario=17,
            ciudad=city,
            calle="Calle 10",
            numero="20",
        )
        self.pending = EstadoPedido.objects.create(nombre="Pendiente de pago")
        self.order = Pedido.objects.create(
            usuario=17,
            cliente_nombre="Cliente Demo",
            cliente_email="cliente@example.test",
            direccion=address,
            estado=self.pending,
            total="480000.00",
        )
        DetallePedido.objects.create(
            pedido=self.order,
            producto=21,
            producto_nombre="Cortina Blackout",
            cantidad=1,
            ancho_cm="100.00",
            alto_cm="200.00",
            area_m2="2.0000",
            precio_m2="240000.00",
            precio_total="480000.00",
        )
        notification_patcher = patch(
            "pedidos.views.requests.post",
            return_value=Mock(
                raise_for_status=Mock(),
                json=lambda: {
                    "pedido_id": self.order.pedido_id,
                    "admin_estado": "enviado",
                    "cliente_estado": "enviado",
                    "estado": "enviado",
                },
            ),
        )
        self.notification_post = notification_patcher.start()
        self.addCleanup(notification_patcher.stop)

    def test_internal_payment_result_updates_order_state(self):
        response = self.client.post(
            f"/api/internal/pedidos/{self.order.pk}/payment-result/",
            {
                "outcome": "approved",
                "payment_reference": "demo-reference-31",
                "amount": "480000.00",
            },
            format="json",
            HTTP_X_INTERNAL_SERVICE_TOKEN="internal-test-token",
        )

        self.assertEqual(response.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.estado.nombre, "Pendiente de preparación")
        self.assertEqual(self.order.referencia_pago, "demo-reference-31")
        self.notification_post.assert_called_once()
        self.assertIn(
            "/api/internal/notificaciones/pedidos/",
            self.notification_post.call_args.args[0],
        )
        self.assertEqual(
            self.notification_post.call_args.kwargs["json"]["detalles"][0][
                "producto_nombre"
            ],
            "Cortina Blackout",
        )

    def test_expired_unpaid_order_is_rejected_and_customer_is_notified(self):
        self.order.fecha_pedido = timezone.now() - timedelta(minutes=5, seconds=1)
        self.order.save(update_fields=["fecha_pedido"])

        call_command("expire_unpaid_orders")

        self.order.refresh_from_db()
        self.assertEqual(self.order.estado.nombre, "Pago rechazado")
        self.assertTrue(
            HistorialEstadoPedido.objects.filter(
                pedido=self.order,
                notas_cambio__contains="venció el plazo de cinco minutos",
            ).exists()
        )
        self.notification_post.assert_called_once()
        self.assertIn(
            "/api/internal/notificaciones/pedidos/estado/",
            self.notification_post.call_args.args[0],
        )
        self.assertEqual(
            self.notification_post.call_args.kwargs["json"]["estado_nuevo"],
            "Pago rechazado",
        )

    def test_payment_context_rejects_expired_order_and_prevents_late_payment(self):
        self.order.fecha_pedido = timezone.now() - timedelta(minutes=5, seconds=1)
        self.order.save(update_fields=["fecha_pedido"])

        response = self.client.get(
            f"/api/internal/pedidos/{self.order.pk}/payment-context/",
            HTTP_X_INTERNAL_SERVICE_TOKEN="internal-test-token",
        )

        self.assertEqual(response.status_code, 409)
        self.order.refresh_from_db()
        self.assertEqual(self.order.estado.nombre, "Pago rechazado")
        self.notification_post.assert_called_once()

    def test_late_payment_result_rejects_order_without_admin_payment_notice(self):
        self.order.fecha_pedido = timezone.now() - timedelta(minutes=5, seconds=1)
        self.order.save(update_fields=["fecha_pedido"])

        response = self.client.post(
            f"/api/internal/pedidos/{self.order.pk}/payment-result/",
            {
                "outcome": "approved",
                "payment_reference": "late-reference",
                "amount": "480000.00",
            },
            format="json",
            HTTP_X_INTERNAL_SERVICE_TOKEN="internal-test-token",
        )

        self.assertEqual(response.status_code, 409)
        self.order.refresh_from_db()
        self.assertEqual(self.order.estado.nombre, "Pago rechazado")
        self.assertIn(
            "/api/internal/notificaciones/pedidos/estado/",
            self.notification_post.call_args.args[0],
        )

    def test_internal_payment_result_rejects_amount_mismatch(self):
        response = self.client.post(
            f"/api/internal/pedidos/{self.order.pk}/payment-result/",
            {
                "outcome": "approved",
                "payment_reference": "demo-reference-32",
                "amount": "1.00",
            },
            format="json",
            HTTP_X_INTERNAL_SERVICE_TOKEN="internal-test-token",
        )

        self.assertEqual(response.status_code, 400)
        self.order.refresh_from_db()
        self.assertEqual(self.order.estado.nombre, self.pending.nombre)

    def test_repeating_a_declined_payment_result_does_not_duplicate_history(self):
        payload = {
            "outcome": "declined",
            "payment_reference": "demo-reference-33",
            "amount": "480000.00",
        }
        first = self.client.post(
            f"/api/internal/pedidos/{self.order.pk}/payment-result/",
            payload,
            format="json",
            HTTP_X_INTERNAL_SERVICE_TOKEN="internal-test-token",
        )
        second = self.client.post(
            f"/api/internal/pedidos/{self.order.pk}/payment-result/",
            payload,
            format="json",
            HTTP_X_INTERNAL_SERVICE_TOKEN="internal-test-token",
        )

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertTrue(second.data["duplicate"])
        self.assertEqual(
            HistorialEstadoPedido.objects.filter(pedido=self.order).count(),
            1,
        )

    def test_declined_payment_is_not_reported_as_admin_sales(self):
        declined = self.client.post(
            f"/api/internal/pedidos/{self.order.pk}/payment-result/",
            {
                "outcome": "declined",
                "payment_reference": "demo-reference-34",
                "amount": "480000.00",
            },
            format="json",
            HTTP_X_INTERNAL_SERVICE_TOKEN="internal-test-token",
        )
        dashboard = self.client.get(
            "/api/internal/pedidos/dashboard/",
            HTTP_X_INTERNAL_SERVICE_TOKEN="internal-test-token",
        )

        self.assertEqual(declined.status_code, 200)
        self.assertEqual(dashboard.status_code, 200)
        self.assertEqual(dashboard.data["pedidos_mes_count"], 0)
        self.assertEqual(dashboard.data["ingresos_mes"], 0.0)
        self.assertEqual(dashboard.data["pedidos_recientes"], [])
