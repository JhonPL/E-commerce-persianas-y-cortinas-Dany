from unittest.mock import Mock, patch

from django.core.management import call_command
from django.test import override_settings
from rest_framework.test import APITestCase

from .models import Categoria, ImagenProducto, Producto


@override_settings(
    INTERNAL_SERVICE_TOKEN="internal-test-token",
    AUTH_SERVICE_URL="http://identity.test/api/v1/auth/me/",
)
class CatalogServiceTests(APITestCase):
    def setUp(self):
        self.category = Categoria.objects.create(nombre="Persianas")
        self.active_product = Producto.objects.create(
            nombre="Blackout",
            precio_m2="120000.00",
            categoria=self.category,
            activo=True,
        )
        self.inactive_product = Producto.objects.create(
            nombre="Producto inactivo",
            precio_m2="90000.00",
            categoria=self.category,
            activo=False,
        )

    def test_public_product_list_contains_only_active_products(self):
        response = self.client.get("/api/v1/catalogo/productos/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [item["producto_id"] for item in response.data["results"]],
            [self.active_product.pk],
        )

    @patch("catalogo.authentication.requests.get")
    def test_admin_product_list_includes_inactive_products(self, get_identity):
        get_identity.return_value = Mock(
            status_code=200,
            json=lambda: {"usuario_id": 4, "rol_nombre": "admin"},
        )

        response = self.client.get(
            "/api/v1/catalogo/productos/",
            HTTP_AUTHORIZATION="Bearer valid-user-token",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 2)

    def test_internal_product_lookup_requires_service_token(self):
        denied = self.client.get(
            "/api/internal/catalogo/productos/?ids=1"
        )
        allowed = self.client.get(
            "/api/internal/catalogo/productos/?ids=1,2",
            HTTP_X_INTERNAL_SERVICE_TOKEN="internal-test-token",
        )

        self.assertEqual(denied.status_code, 401)
        self.assertEqual(allowed.status_code, 200)
        self.assertEqual(len(allowed.data), 2)

    @patch("catalogo.authentication.requests.get")
    def test_product_delete_uses_catalog_service_only(self, get_identity):
        get_identity.return_value = Mock(
            status_code=200,
            json=lambda: {"usuario_id": 4, "rol_nombre": "admin"},
        )
        response = self.client.delete(
            f"/api/v1/catalogo/productos/{self.active_product.pk}/",
            HTTP_AUTHORIZATION="Bearer valid-user-token",
        )

        self.assertEqual(response.status_code, 204)
        self.assertFalse(Producto.objects.filter(pk=self.active_product.pk).exists())

    def test_demo_seed_creates_products_only_when_catalog_is_empty(self):
        Producto.objects.all().delete()

        call_command("seed_demo_catalog")
        call_command("seed_demo_catalog")

        self.assertEqual(Producto.objects.count(), 5)
        self.assertEqual(ImagenProducto.objects.count(), 5)
