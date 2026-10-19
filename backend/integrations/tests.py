from unittest.mock import patch

import requests
from django.test import SimpleTestCase, override_settings
from rest_framework.test import APIClient

from integrations.identity import (
    IdentityServiceUnavailable,
    RemoteIdentityAuthentication,
    get_identity_dashboard,
)
from usuarios.models import Rol


@override_settings(
    IDENTITY_SERVICE_URL="http://identity.test",
    IDENTITY_SERVICE_TIMEOUT_SECONDS=3,
    INTERNAL_SERVICE_TOKEN="shared-test-token",
)
class IdentityIntegrationTests(SimpleTestCase):
    @patch("integrations.identity.requests.get")
    def test_remote_authentication_builds_user_from_identity_contract(self, get):
        get.return_value.status_code = 200
        get.return_value.json.return_value = {
            "usuario_id": 23,
            "nombre": "Admin",
            "email": "admin@example.com",
            "rol_nombre": Rol.ADMIN,
        }
        request = APIClient().get(
            "/",
            HTTP_AUTHORIZATION="Bearer sample-token",
        ).wsgi_request

        user, token = RemoteIdentityAuthentication().authenticate(request)

        self.assertEqual(user.usuario_id, 23)
        self.assertTrue(user.is_staff)
        self.assertEqual(token, "Bearer sample-token")
        get.assert_called_once_with(
            "http://identity.test/api/v1/auth/me/",
            headers={"Authorization": "Bearer sample-token"},
            timeout=3,
        )

    @patch("integrations.identity.requests.get")
    def test_dashboard_summary_uses_internal_identity_endpoint(self, get):
        get.return_value.status_code = 200
        get.return_value.json.return_value = {
            "total_clientes": 8,
            "clientes_mes": 3,
            "clientes_mes_anterior": 2,
        }

        data = get_identity_dashboard()

        self.assertEqual(data["total_clientes"], 8)
        get.assert_called_once_with(
            "http://identity.test/api/internal/identity/resumen/",
            headers={"X-Internal-Service-Token": "shared-test-token"},
            timeout=3,
        )

    @patch("integrations.identity.requests.get")
    def test_dashboard_authentication_and_metrics_use_remote_identity(self, get):
        get.return_value.status_code = 200
        get.return_value.json.return_value = {
            "usuario_id": 23,
            "nombre": "Admin",
            "email": "admin@example.com",
            "rol_nombre": Rol.ADMIN,
        }
        with (
            patch(
                "pedidos.views.get_orders_dashboard",
                return_value={
                    "periodo_label": "junio",
                    "pedidos_mes_count": 1,
                    "pct_pedidos": "0",
                    "ingresos_mes": 100,
                    "pct_ingresos": "0",
                    "pendientes_48h": 0,
                    "ventas_mes": [],
                    "pedidos_recientes": [],
                    "top_productos": [],
                },
            ),
            patch(
                "pedidos.views.get_identity_dashboard",
                return_value={
                    "total_clientes": 8,
                    "clientes_mes": 3,
                    "clientes_mes_anterior": 2,
                },
            ),
            patch(
                "pedidos.views.get_catalog_summary",
                return_value={
                    "productos_activos": 5,
                    "productos_sin_imagen_principal": 0,
                },
            ),
        ):
            response = APIClient().get(
                "/api/v1/admin/dashboard/",
                HTTP_AUTHORIZATION="Bearer sample-token",
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["metrics"]["clientes"]["value"], 8)
        self.assertEqual(response.data["metrics"]["clientes"]["delta"], "+1")

    @patch("integrations.identity.requests.get")
    def test_identity_unavailability_is_not_treated_as_anonymous(self, get):
        get.side_effect = requests.ConnectionError("network is unavailable")
        request = APIClient().get(
            "/",
            HTTP_AUTHORIZATION="Bearer sample-token",
        ).wsgi_request

        with self.assertRaises(IdentityServiceUnavailable):
            RemoteIdentityAuthentication().authenticate(request)

    @patch("service_proxy.requests.request")
    def test_auth_and_admin_user_routes_proxy_to_identity_service(self, upstream):
        upstream.return_value.status_code = 200
        upstream.return_value.content = b'{"ok":true}'
        upstream.return_value.headers = {"Content-Type": "application/json"}
        client = APIClient()

        auth_response = client.post(
            "/api/v1/auth/login/",
            {"email": "ana@example.com", "password": "secret"},
            format="json",
        )
        admin_response = client.patch(
            "/api/v1/admin/usuarios/41/activo/",
            {"activo": False},
            format="json",
        )

        self.assertEqual(auth_response.status_code, 200)
        self.assertEqual(admin_response.status_code, 200)
        self.assertEqual(
            [call.args[1] for call in upstream.call_args_list],
            [
                "http://identity.test/api/v1/auth/login/",
                "http://identity.test/api/v1/admin/usuarios/41/activo/",
            ],
        )
