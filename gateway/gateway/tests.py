from unittest.mock import Mock, patch

import requests

from django.test import SimpleTestCase, override_settings


class GatewayHealthTests(SimpleTestCase):
    def test_health_endpoint_is_live(self):
        response = self.client.get("/health/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok", "service": "gateway"})


@override_settings(
    CATALOGO_SERVICE_URL="http://catalog.test/api/v1/catalogo",
    SERVICE_TIMEOUT_SECONDS=3,
)
class ServiceProxyTests(SimpleTestCase):
    @patch("gateway.proxies.requests.request")
    def test_proxy_forwards_route_query_and_authentication(self, request):
        request.return_value = Mock(
            content=b'{"results":[]}',
            status_code=200,
            headers={"Content-Type": "application/json"},
        )

        response = self.client.get(
            "/api/v1/catalogo/productos/?search=velo",
            HTTP_AUTHORIZATION="Bearer customer-token",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'{"results":[]}')
        self.assertEqual(
            request.call_args.args[:2],
            ("GET", "http://catalog.test/api/v1/catalogo/productos/"),
        )
        self.assertEqual(request.call_args.kwargs["params"], [("search", "velo")])
        self.assertEqual(
            request.call_args.kwargs["headers"]["Authorization"],
            "Bearer customer-token",
        )


@override_settings(
    ORDERS_SERVICE_URL="http://orders.test",
    SERVICE_TIMEOUT_SECONDS=3,
    ORDERS_SERVICE_TIMEOUT_SECONDS=30,
)
class OrdersServiceProxyTests(SimpleTestCase):
    @patch("gateway.proxies.requests.request")
    def test_checkout_proxy_uses_extended_orders_timeout(self, request):
        request.return_value = Mock(
            content=b'{"pedido_id":42}',
            status_code=201,
            headers={"Content-Type": "application/json"},
        )

        response = self.client.post(
            "/api/v1/pedidos/checkout/",
            data='{"direccion":{}}',
            content_type="application/json",
            HTTP_AUTHORIZATION="Bearer customer-token",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            request.call_args.args[:2],
            ("POST", "http://orders.test/api/v1/pedidos/checkout/"),
        )
        self.assertEqual(request.call_args.kwargs["timeout"], 30)


@override_settings(
    NOTIFICATIONS_SERVICE_URL="http://notifications.test",
    INTERNAL_SERVICE_TOKEN="gateway-internal-test-token",
    SERVICE_TIMEOUT_SECONDS=3,
)
class ContactNotificationProxyTests(SimpleTestCase):
    @patch("gateway.views.requests.post")
    def test_contact_form_is_forwarded_with_internal_token(self, post):
        post.return_value = Mock(
            content=b'{"estado":"enviado"}',
            status_code=200,
            headers={"Content-Type": "application/json"},
        )

        response = self.client.post(
            "/api/v1/contacto/",
            data='{"nombre":"Cliente","email":"cliente@example.com","mensaje":"Hola"}',
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'{"estado":"enviado"}')
        self.assertEqual(
            post.call_args.args,
            ("http://notifications.test/api/internal/notificaciones/contacto/",),
        )
        self.assertEqual(
            post.call_args.kwargs["headers"]["X-Internal-Service-Token"],
            "gateway-internal-test-token",
        )
        self.assertEqual(
            post.call_args.kwargs["data"],
            b'{"nombre":"Cliente","email":"cliente@example.com","mensaje":"Hola"}',
        )

    @patch(
        "gateway.views.requests.post",
        side_effect=requests.ConnectionError("offline"),
    )
    def test_contact_form_reports_notification_service_unavailability(self, post):
        response = self.client.post(
            "/api/v1/contacto/",
            data='{"nombre":"Cliente","email":"cliente@example.com","mensaje":"Hola"}',
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json()["detail"],
            "El servicio de notificaciones no está disponible.",
        )


@override_settings(
    IDENTITY_SERVICE_URL="http://identity.test",
    ORDERS_SERVICE_URL="http://orders.test",
    CATALOGO_SERVICE_INTERNAL_URL="http://catalog.test/api/internal/catalogo",
    INTERNAL_SERVICE_TOKEN="gateway-internal-test-token",
)
class AdminDashboardTests(SimpleTestCase):
    @patch("gateway.views._service_summary")
    @patch("gateway.views._get_json")
    def test_dashboard_combines_service_owned_metrics(self, get_json, summary):
        get_json.return_value = {"rol_nombre": "admin"}
        summary.side_effect = [
            {
                "periodo_label": "Oct 2026",
                "pedidos_mes_count": 2,
                "pedidos_prev_count": 1,
                "ingresos_mes": 200000.0,
                "pct_pedidos": "+100%",
                "pct_ingresos": "+100%",
                "ventas_mes": [],
                "pedidos_recientes": [],
                "top_productos": [],
                "pendientes_48h": 0,
            },
            {
                "total_clientes": 9,
                "clientes_mes": 2,
                "clientes_mes_anterior": 1,
            },
            {
                "productos_activos": 2,
                "productos_sin_imagen_principal": 1,
            },
        ]
        response = self.client.get(
            "/api/v1/admin/dashboard/",
            HTTP_AUTHORIZATION="Bearer admin-token",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["metrics"]["clientes"]["value"], 9)
        self.assertEqual(response.json()["metrics"]["clientes"]["delta"], "+1")
        self.assertEqual(len(response.json()["alertas"]), 1)

    @patch("gateway.views._get_json")
    def test_dashboard_rejects_non_admin_user(self, get_json):
        get_json.return_value = {"rol_nombre": "cliente"}

        response = self.client.get(
            "/api/v1/admin/dashboard/",
            HTTP_AUTHORIZATION="Bearer customer-token",
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["detail"], "No autorizado.")


@override_settings(
    IDENTITY_SERVICE_URL="http://identity.test",
    ORDERS_SERVICE_URL="http://orders.test",
    CART_SERVICE_INTERNAL_URL="http://cart.test/api/internal/carrito",
    CATALOGO_SERVICE_URL="http://catalog.test/api/v1/catalogo",
    INTERNAL_SERVICE_TOKEN="gateway-internal-test-token",
)
class ProductDeletionTests(SimpleTestCase):
    @patch("gateway.views.requests.get")
    def test_deletion_is_blocked_when_product_has_order_references(self, get):
        get.side_effect = [
            Mock(status_code=200, json=lambda: {"rol_nombre": "admin"}),
            Mock(status_code=409),
        ]

        response = self.client.delete(
            "/api/v1/catalogo/productos/21/",
            HTTP_AUTHORIZATION="Bearer admin-token",
        )

        self.assertEqual(response.status_code, 409)

    @patch("gateway.views.requests.delete")
    @patch("gateway.views.requests.get")
    def test_deletion_cleans_cart_after_reference_check(self, get, delete):
        get.side_effect = [
            Mock(status_code=200, json=lambda: {"rol_nombre": "admin"}),
            Mock(status_code=200),
        ]
        delete.side_effect = [
            Mock(status_code=204),
            Mock(status_code=204, content=b"", headers={}),
        ]

        response = self.client.delete(
            "/api/v1/catalogo/productos/21/",
            HTTP_AUTHORIZATION="Bearer admin-token",
        )

        self.assertEqual(response.status_code, 204)
        self.assertEqual(delete.call_count, 2)

    @patch("gateway.views.requests.get")
    @patch("gateway.views.requests.delete")
    def test_deletion_rejects_non_admin_before_cleanup(self, delete, get):
        get.return_value = Mock(
            status_code=200,
            json=lambda: {"rol_nombre": "cliente"},
        )

        response = self.client.delete(
            "/api/v1/catalogo/productos/21/",
            HTTP_AUTHORIZATION="Bearer customer-token",
        )

        self.assertEqual(response.status_code, 403)
        delete.assert_not_called()
