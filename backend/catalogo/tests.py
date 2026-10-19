from decimal import Decimal
from unittest.mock import Mock, patch

from cart_service_proxy import CartServiceProxy
from django.core.management.base import CommandError
from django.test import Client, RequestFactory, SimpleTestCase, override_settings

from catalog_service_proxy import CatalogServiceProxy
from orders_service_proxy import OrdersServiceProxy
from integrations.catalogo import (
    CatalogServiceUnavailable,
    get_catalog_products,
)
from integrations.pedidos import OrdersServiceUnavailable, get_orders_dashboard
from integrations.views import prepare_product_deletion
from usuarios.management.commands.seed_demo import Command as SeedDemoCommand


class CatalogServiceProxyTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    @override_settings(
        CATALOGO_SERVICE_URL="http://catalog.test/api/v1/catalogo",
        CATALOGO_SERVICE_TIMEOUT_SECONDS=7,
    )
    @patch("service_proxy.requests.request")
    def test_forwards_catalog_request_and_user_authorization(self, upstream_request):
        upstream_request.return_value = Mock(
            status_code=201,
            content=b'{"producto_id": 12}',
            headers={"Content-Type": "application/json"},
        )
        request = self.factory.post(
            "/api/v1/catalogo/productos/",
            data='{"nombre":"Persiana"}',
            content_type="application/json",
            HTTP_AUTHORIZATION="Bearer user-token",
        )

        response = CatalogServiceProxy.as_view()(request, subpath="productos")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.content, b'{"producto_id": 12}')
        upstream_request.assert_called_once_with(
            "POST",
            "http://catalog.test/api/v1/catalogo/productos/",
            params=[],
            data=b'{"nombre":"Persiana"}',
            headers={
                "Authorization": "Bearer user-token",
                "Content-Type": "application/json",
            },
            timeout=7,
            allow_redirects=False,
        )

    @override_settings(
        CATALOGO_SERVICE_URL="http://catalog.test/api/v1/catalogo"
    )
    @patch("service_proxy.requests.request")
    def test_reports_unavailable_catalog_service(self, upstream_request):
        import requests

        upstream_request.side_effect = requests.ConnectionError()
        request = self.factory.get("/api/v1/catalogo/productos/")

        response = CatalogServiceProxy.as_view()(request, subpath="productos")

        self.assertEqual(response.status_code, 503)
        self.assertIn(b"no est", response.content)


class CartServiceProxyTests(SimpleTestCase):
    @override_settings(
        CART_SERVICE_URL="http://cart.test/api/v1/carrito",
        CART_SERVICE_TIMEOUT_SECONDS=6,
    )
    @patch("service_proxy.requests.request")
    def test_forwards_cart_request_and_user_authorization(self, upstream_request):
        upstream_request.return_value = Mock(
            status_code=200,
            content=b'{"items":[],"total_items":0,"total":0.0}',
            headers={"Content-Type": "application/json"},
        )
        request = RequestFactory().post(
            "/api/v1/carrito/",
            data='{"producto":12}',
            content_type="application/json",
            HTTP_AUTHORIZATION="******",
        )

        response = CartServiceProxy.as_view()(request, subpath="")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.content,
            b'{"items":[],"total_items":0,"total":0.0}',
        )
        upstream_request.assert_called_once_with(
            "POST",
            "http://cart.test/api/v1/carrito/",
            params=[],
            data=b'{"producto":12}',
            headers={
                "Authorization": "******",
                "Content-Type": "application/json",
            },
            timeout=6,
            allow_redirects=False,
        )


class OrdersServiceProxyTests(SimpleTestCase):
    @override_settings(
        ORDERS_SERVICE_URL="http://orders.test",
        ORDERS_SERVICE_TIMEOUT_SECONDS=6,
    )
    @patch("service_proxy.requests.request")
    def test_preserves_customer_order_url_through_proxy(self, upstream_request):
        upstream_request.return_value = Mock(
            status_code=200,
            content=b'{"pedido_id":12}',
            headers={"Content-Type": "application/json"},
        )
        request = RequestFactory().get(
            "/api/v1/pedidos/12/",
            HTTP_AUTHORIZATION="Bearer user-token",
        )

        response = OrdersServiceProxy.as_view()(
            request,
            prefixes=("api", "v1", "pedidos"),
            subpath="12",
        )

        self.assertEqual(response.status_code, 200)
        upstream_request.assert_called_once_with(
            "GET",
            "http://orders.test/api/v1/pedidos/12/",
            params=[],
            data=None,
            headers={"Authorization": "Bearer user-token"},
            timeout=6,
            allow_redirects=False,
        )

    @override_settings(
        ORDERS_SERVICE_URL="http://orders.test",
        ORDERS_SERVICE_TIMEOUT_SECONDS=6,
    )
    @patch("service_proxy.requests.request")
    def test_configured_customer_route_adds_upstream_path(self, upstream_request):
        upstream_request.return_value = Mock(
            status_code=200,
            content=b'{"pedidos":[],"total":0}',
            headers={"Content-Type": "application/json"},
        )

        response = Client().get("/api/v1/pedidos/")

        self.assertEqual(response.status_code, 200)
        upstream_request.assert_called_once_with(
            "GET",
            "http://orders.test/api/v1/pedidos/",
            params=[],
            data=None,
            headers={},
            timeout=6,
            allow_redirects=False,
        )

    @override_settings(
        ORDERS_SERVICE_URL="http://orders.test",
        ORDERS_SERVICE_TIMEOUT_SECONDS=6,
    )
    @patch("service_proxy.requests.request")
    def test_configured_admin_order_route_preserves_filters(
        self, upstream_request
    ):
        upstream_request.return_value = Mock(
            status_code=200,
            content=b'{"pedidos":[],"total":0}',
            headers={"Content-Type": "application/json"},
        )

        response = Client().get(
            "/api/v1/admin/pedidos/?estado=2&page=3",
        )

        self.assertEqual(response.status_code, 200)
        upstream_request.assert_called_once_with(
            "GET",
            "http://orders.test/api/v1/admin/pedidos/",
            params=[("estado", "2"), ("page", "3")],
            data=None,
            headers={},
            timeout=6,
            allow_redirects=False,
        )


class CatalogIntegrationTests(SimpleTestCase):
    @override_settings(
        CATALOGO_SERVICE_INTERNAL_URL="http://catalog.test/api/internal/catalogo",
        CATALOGO_SERVICE_TIMEOUT_SECONDS=4,
        INTERNAL_SERVICE_TOKEN="test-service-token",
    )
    @patch("integrations.catalogo.requests.get")
    def test_catalog_lookup_uses_internal_token_and_indexes_products(
        self, upstream_get
    ):
        upstream_get.return_value = Mock(
            raise_for_status=Mock(),
            json=lambda: [
                {"producto_id": 12, "nombre": "Persiana"},
                {"producto_id": 8, "nombre": "Cortina"},
            ],
        )

        products = get_catalog_products([12, 8])

        self.assertEqual(products[12]["nombre"], "Persiana")
        self.assertEqual(products[8]["nombre"], "Cortina")
        self.assertEqual(
            upstream_get.call_args.kwargs["headers"],
            {"X-Internal-Service-Token": "test-service-token"},
        )

    @override_settings(
        CATALOGO_SERVICE_INTERNAL_URL="http://catalog.test/api/internal/catalogo",
        CATALOGO_SERVICE_TIMEOUT_SECONDS=4,
        INTERNAL_SERVICE_TOKEN="test-service-token",
    )
    @patch("integrations.catalogo.requests.get")
    def test_catalog_lookup_rejects_missing_product(self, upstream_get):
        upstream_get.return_value = Mock(
            raise_for_status=Mock(),
            json=lambda: [{"producto_id": 8, "nombre": "Cortina"}],
        )

        with self.assertRaises(CatalogServiceUnavailable):
            get_catalog_products([8, 12])


class SeedDemoCatalogIntegrationTests(SimpleTestCase):
    @override_settings(
        CATALOGO_SERVICE_URL="http://catalog.test/api/v1/catalogo",
        CATALOGO_SERVICE_TIMEOUT_SECONDS=4,
    )
    @patch("usuarios.management.commands.seed_demo.requests.get")
    def test_seed_demo_reads_products_from_catalog_service(self, upstream_get):
        upstream_get.return_value = Mock(
            raise_for_status=Mock(),
            json=lambda: {
                "results": [
                    {"producto_id": "12", "precio_m2": "25000.00"},
                    {"producto_id": 8, "precio_m2": 30000},
                ]
            },
        )

        products = SeedDemoCommand().get_catalog_products()

        self.assertEqual(
            products,
            [
                {"producto_id": 12, "precio_m2": Decimal("25000.00")},
                {"producto_id": 8, "precio_m2": Decimal("30000")},
            ],
        )
        upstream_get.assert_called_once_with(
            "http://catalog.test/api/v1/catalogo/productos/",
            params={"page": 1, "page_size": 100},
            timeout=4,
        )

    @patch("usuarios.management.commands.seed_demo.requests.get")
    def test_seed_demo_rejects_invalid_catalog_response(self, upstream_get):
        upstream_get.return_value = Mock(
            raise_for_status=Mock(),
            json=lambda: {"results": [{"producto_id": 12}]},
        )

        with self.assertRaises(CommandError):
            SeedDemoCommand().get_catalog_products()


class OrdersDashboardIntegrationTests(SimpleTestCase):
    @override_settings(
        ORDERS_SERVICE_URL="http://orders.test",
        ORDERS_SERVICE_TIMEOUT_SECONDS=4,
        INTERNAL_SERVICE_TOKEN="orders-token",
    )
    @patch("integrations.pedidos.requests.get")
    def test_dashboard_uses_internal_service_token(self, upstream_get):
        dashboard = {
            "periodo_label": "Oct 2026",
            "pedidos_mes_count": 2,
            "pedidos_prev_count": 1,
            "ingresos_mes": 400.0,
            "ingresos_prev": 200.0,
            "ventas_mes": [],
            "pedidos_recientes": [],
            "top_productos": [],
            "pendientes_48h": 0,
            "pct_pedidos": "+100%",
            "pct_ingresos": "+100%",
        }
        upstream_get.return_value = Mock(
            raise_for_status=Mock(),
            json=lambda: dashboard,
        )

        result = get_orders_dashboard()

        self.assertEqual(result, dashboard)
        upstream_get.assert_called_once_with(
            "http://orders.test/api/internal/pedidos/dashboard/",
            headers={"X-Internal-Service-Token": "orders-token"},
            timeout=4,
        )

    @override_settings(
        ORDERS_SERVICE_URL="http://orders.test",
        ORDERS_SERVICE_TIMEOUT_SECONDS=4,
        INTERNAL_SERVICE_TOKEN="orders-token",
    )
    @patch("integrations.pedidos.requests.get")
    def test_dashboard_rejects_incomplete_response(self, upstream_get):
        upstream_get.return_value = Mock(
            raise_for_status=Mock(),
            json=lambda: {},
        )

        with self.assertRaises(OrdersServiceUnavailable):
            get_orders_dashboard()


class ProductReferenceDeletionTests(SimpleTestCase):
    @override_settings(
        INTERNAL_SERVICE_TOKEN="test-service-token",
        ORDERS_SERVICE_URL="http://orders.test",
        ORDERS_SERVICE_TIMEOUT_SECONDS=3,
    )
    @patch("integrations.views.requests.get")
    @patch("integrations.views.requests.delete")
    def test_deletion_is_blocked_when_orders_reference_product(
        self, cart_delete, order_check
    ):
        order_check.return_value = Mock(status_code=409)
        request = RequestFactory().delete(
            "/api/internal/catalogo/productos/12/",
            HTTP_X_INTERNAL_SERVICE_TOKEN="test-service-token",
        )

        response = prepare_product_deletion(request, product_id=12)

        self.assertEqual(response.status_code, 409)
        cart_delete.assert_not_called()

    @override_settings(
        INTERNAL_SERVICE_TOKEN="test-service-token",
        ORDERS_SERVICE_URL="http://orders.test",
        ORDERS_SERVICE_TIMEOUT_SECONDS=3,
        CART_SERVICE_INTERNAL_URL="http://cart.test/api/internal/carrito",
        CART_SERVICE_TIMEOUT_SECONDS=3,
    )
    @patch("integrations.views.requests.get")
    @patch("integrations.views.requests.delete")
    def test_deletion_clears_cart_references_when_no_order_uses_product(
        self, cart_delete, order_check
    ):
        order_check.return_value = Mock(status_code=200)
        cart_delete.return_value = Mock(status_code=204)
        request = RequestFactory().delete(
            "/api/internal/catalogo/productos/12/",
            HTTP_X_INTERNAL_SERVICE_TOKEN="test-service-token",
        )

        response = prepare_product_deletion(request, product_id=12)

        self.assertEqual(response.status_code, 204)
        order_check.assert_called_once_with(
            "http://orders.test/api/internal/pedidos/productos/12/",
            headers={"X-Internal-Service-Token": "test-service-token"},
            timeout=3,
        )
        cart_delete.assert_called_once_with(
            "http://cart.test/api/internal/carrito/productos/12/",
            headers={"X-Internal-Service-Token": "test-service-token"},
            timeout=3,
        )

    @override_settings(
        INTERNAL_SERVICE_TOKEN="test-service-token",
        ORDERS_SERVICE_URL="http://orders.test",
        ORDERS_SERVICE_TIMEOUT_SECONDS=3,
        CART_SERVICE_INTERNAL_URL="http://cart.test/api/internal/carrito",
        CART_SERVICE_TIMEOUT_SECONDS=3,
    )
    @patch("integrations.views.requests.get")
    @patch("integrations.views.requests.delete")
    def test_deletion_fails_explicitly_if_cart_service_is_unavailable(
        self, cart_delete, order_check
    ):
        import requests

        order_check.return_value = Mock(status_code=200)
        cart_delete.side_effect = requests.ConnectionError()
        request = RequestFactory().delete(
            "/api/internal/catalogo/productos/12/",
            HTTP_X_INTERNAL_SERVICE_TOKEN="test-service-token",
        )

        response = prepare_product_deletion(request, product_id=12)

        self.assertEqual(response.status_code, 503)

    @override_settings(
        INTERNAL_SERVICE_TOKEN="test-service-token",
        ORDERS_SERVICE_URL="http://orders.test",
        ORDERS_SERVICE_TIMEOUT_SECONDS=3,
    )
    @patch("integrations.views.requests.get")
    def test_deletion_fails_closed_if_orders_service_is_unavailable(
        self, order_check
    ):
        import requests

        order_check.side_effect = requests.ConnectionError()
        request = RequestFactory().delete(
            "/api/internal/catalogo/productos/12/",
            HTTP_X_INTERNAL_SERVICE_TOKEN="test-service-token",
        )

        response = prepare_product_deletion(request, product_id=12)

        self.assertEqual(response.status_code, 503)
    @override_settings(INTERNAL_SERVICE_TOKEN="test-service-token")
    def test_deletion_rejects_invalid_service_token(self):
        request = RequestFactory().delete(
            "/api/internal/catalogo/productos/12/",
            HTTP_X_INTERNAL_SERVICE_TOKEN="wrong-token",
        )

        response = prepare_product_deletion(request, product_id=12)

        self.assertEqual(response.status_code, 403)
