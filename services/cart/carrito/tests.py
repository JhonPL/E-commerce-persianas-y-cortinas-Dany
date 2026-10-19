from unittest.mock import Mock, patch

from django.test import override_settings
from rest_framework.test import APIClient, APITestCase

from .authentication import RemoteUser
from .models import CarritoItem


@override_settings(
    INTERNAL_SERVICE_TOKEN="internal-test-token",
    AUTH_SERVICE_URL="http://identity.test/api/v1/auth/me/",
    CATALOGO_SERVICE_INTERNAL_URL="http://catalog.test/api/internal/catalogo",
)
class CartServiceTests(APITestCase):
    def setUp(self):
        self.client.force_authenticate(user=RemoteUser(17, "cliente"))
        self.active_product = {
            "producto_id": 21,
            "nombre": "Blackout",
            "precio_m2": "120000.00",
            "imagen_principal": "https://images.test/blackout.jpg",
            "activo": True,
        }

    @patch("carrito.catalog.requests.get")
    def test_cart_list_preserves_public_response_shape(self, catalog_get):
        item = CarritoItem.objects.create(
            usuario=17,
            producto=21,
            cantidad=2,
            ancho_cm="100.00",
            alto_cm="200.00",
        )
        catalog_get.return_value = Mock(
            raise_for_status=Mock(),
            json=lambda: [self.active_product],
        )

        response = self.client.get("/api/v1/carrito/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total_items"], 1)
        self.assertEqual(response.data["total"], 480000.0)
        self.assertEqual(response.data["items"][0]["item_id"], item.pk)
        self.assertEqual(response.data["items"][0]["nombre"], "Blackout")
        catalog_get.assert_called_once()

    @patch("carrito.catalog.requests.get")
    def test_add_item_merges_same_product_and_measurements(self, catalog_get):
        catalog_get.return_value = Mock(
            raise_for_status=Mock(),
            json=lambda: [self.active_product],
        )
        item = CarritoItem.objects.create(
            usuario=17,
            producto=21,
            cantidad=1,
            ancho_cm="100.00",
            alto_cm="200.00",
        )

        response = self.client.post(
            "/api/v1/carrito/",
            {
                "producto": 21,
                "cantidad": 3,
                "ancho_cm": "100",
                "alto_cm": "200",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        item.refresh_from_db()
        self.assertEqual(item.cantidad, 4)
        self.assertEqual(response.data["total"], 960000.0)

    @patch("carrito.catalog.requests.get")
    def test_sync_ignores_inactive_products_and_reports_the_item(self, catalog_get):
        inactive_product = {**self.active_product, "activo": False}
        catalog_get.return_value = Mock(
            raise_for_status=Mock(),
            json=lambda: [inactive_product],
        )

        response = self.client.post(
            "/api/v1/carrito/sincronizar/",
            {
                "items": [
                    {
                        "producto": 21,
                        "ancho_cm": 100,
                        "alto_cm": 200,
                        "cantidad": 1,
                    }
                ]
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["items"], [])
        self.assertEqual(
            response.data["errores_items"][0]["indice"],
            0,
        )
        self.assertFalse(CarritoItem.objects.exists())

    def test_internal_product_cleanup_requires_valid_service_token(self):
        internal_client = APIClient()
        denied = internal_client.delete(
            "/api/internal/carrito/productos/21/",
            HTTP_X_INTERNAL_SERVICE_TOKEN="wrong-token",
        )
        allowed = internal_client.delete(
            "/api/internal/carrito/productos/21/",
            HTTP_X_INTERNAL_SERVICE_TOKEN="internal-test-token",
        )

        self.assertEqual(denied.status_code, 401)
        self.assertEqual(allowed.status_code, 204)

    @patch("carrito.authentication.requests.get")
    def test_user_requests_are_validated_by_identity_service(self, identity_get):
        identity_get.return_value = Mock(
            status_code=200,
            json=lambda: {"usuario_id": 17, "rol_nombre": "cliente"},
        )

        response = APIClient().get(
            "/api/v1/carrito/",
            HTTP_AUTHORIZATION="Bearer test-user-token",
        )

        self.assertEqual(response.status_code, 200)
        identity_get.assert_called_once_with(
            "http://identity.test/api/v1/auth/me/",
            headers={"Authorization": "Bearer test-user-token"},
            timeout=5,
        )

    def test_user_cannot_update_another_users_cart_item(self):
        item = CarritoItem.objects.create(
            usuario=22,
            producto=21,
            cantidad=1,
            ancho_cm="100.00",
            alto_cm="200.00",
        )

        response = self.client.delete(f"/api/v1/carrito/{item.pk}/")

        self.assertEqual(response.status_code, 404)
        self.assertTrue(CarritoItem.objects.filter(pk=item.pk).exists())
