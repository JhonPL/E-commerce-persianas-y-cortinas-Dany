import json
import tempfile
import urllib.error
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from django.core.management import call_command
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken

from .models import Cliente, Rol, Usuario


@override_settings(INTERNAL_SERVICE_TOKEN="test-internal-token")
class IdentityApiTests(APITestCase):
    def setUp(self):
        self.customer_role, _ = Rol.objects.get_or_create(nombre=Rol.CLIENTE)
        self.admin_role, _ = Rol.objects.get_or_create(nombre=Rol.ADMIN)

    def test_registration_creates_customer_profile(self):
        response = self.client.post(
            "/api/v1/auth/registro/",
            {
                "nombre": "Ana",
                "email": "ANA@example.com",
                "password": "strong-pass-123",
                "password_confirmar": "strong-pass-123",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = Usuario.objects.get(email="ana@example.com")
        self.assertTrue(user.check_password("strong-pass-123"))
        self.assertEqual(user.rol.nombre, Rol.CLIENTE)
        self.assertTrue(Cliente.objects.filter(usuario=user).exists())
        self.assertNotIn("password", response.data["usuario"])

    def test_login_and_me_use_compatible_user_id_claim(self):
        user = Usuario.objects.create_user(
            email="ana@example.com",
            nombre="Ana",
            password="strong-pass-123",
            rol=self.customer_role,
        )
        response = self.client.post(
            "/api/v1/auth/login/",
            {"email": user.email, "password": "strong-pass-123"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            AccessToken(response.data["access"])["usuario_id"],
            str(user.pk),
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {response.data['access']}"
        )
        me = self.client.get("/api/v1/auth/me/")
        self.assertEqual(me.status_code, status.HTTP_200_OK)
        self.assertEqual(me.data["usuario_id"], user.pk)
        self.assertEqual(me.data["rol_nombre"], Rol.CLIENTE)

    def test_inactive_user_cannot_login_or_use_existing_access_token(self):
        user = Usuario.objects.create_user(
            email="inactive@example.com",
            nombre="Inactive",
            password="strong-pass-123",
            rol=self.customer_role,
        )
        token = str(AccessToken.for_user(user))
        user.activo = False
        user.save(update_fields=["activo"])

        login = self.client.post(
            "/api/v1/auth/login/",
            {"email": user.email, "password": "strong-pass-123"},
            format="json",
        )
        self.assertEqual(login.status_code, status.HTTP_400_BAD_REQUEST)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        me = self.client.get("/api/v1/auth/me/")
        self.assertEqual(me.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_profile_can_be_read_and_updated(self):
        user = Usuario.objects.create_user(
            email="ana@example.com",
            nombre="Ana",
            password="strong-pass-123",
            rol=self.customer_role,
        )
        Cliente.objects.create(usuario=user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(user)}")

        update = self.client.patch(
            "/api/v1/auth/perfil/",
            {"nombre": "Ana María", "telefono": "3001234567"},
            format="json",
        )
        self.assertEqual(update.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertEqual(user.nombre, "Ana María")
        self.assertEqual(user.cliente.telefono, "3001234567")

    def test_internal_summary_requires_shared_service_token(self):
        Usuario.objects.create_user(
            email="ana@example.com",
            nombre="Ana",
            password="strong-pass-123",
            rol=self.customer_role,
        )
        unauthorized = self.client.get("/api/internal/identity/resumen/")
        self.assertEqual(unauthorized.status_code, status.HTTP_401_UNAUTHORIZED)
        authorized = self.client.get(
            "/api/internal/identity/resumen/",
            HTTP_X_INTERNAL_SERVICE_TOKEN="test-internal-token",
        )
        self.assertEqual(authorized.status_code, status.HTTP_200_OK)
        self.assertEqual(authorized.data["total_clientes"], 1)

    def test_admin_can_list_and_deactivate_customer(self):
        admin = Usuario.objects.create_user(
            email="admin@example.com",
            nombre="Admin",
            password="strong-pass-123",
            rol=self.admin_role,
        )
        customer = Usuario.objects.create_user(
            email="ana@example.com",
            nombre="Ana",
            password="strong-pass-123",
            rol=self.customer_role,
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(admin)}"
        )

        listing = self.client.get("/api/v1/admin/usuarios/")
        self.assertEqual(listing.status_code, status.HTTP_200_OK)
        self.assertEqual(listing.data["total"], 2)
        self.assertEqual(
            {row["rol"] for row in listing.data["usuarios"]},
            {Rol.ADMIN, Rol.CLIENTE},
        )

        deactivation = self.client.patch(
            f"/api/v1/admin/usuarios/{customer.pk}/activo/",
            {"activo": False},
            format="json",
        )
        self.assertEqual(deactivation.status_code, status.HTTP_200_OK)
        customer.refresh_from_db()
        self.assertFalse(customer.activo)

    def test_admin_can_promote_customer_and_customer_cannot_change_roles(self):
        admin = Usuario.objects.create_user(
            email="admin@example.com",
            nombre="Admin",
            password="strong-pass-123",
            rol=self.admin_role,
        )
        customer = Usuario.objects.create_user(
            email="ana@example.com",
            nombre="Ana",
            password="strong-pass-123",
            rol=self.customer_role,
        )
        another_customer = Usuario.objects.create_user(
            email="luz@example.com",
            nombre="Luz",
            password="strong-pass-123",
            rol=self.customer_role,
        )

        self.client.force_authenticate(user=admin)
        promotion = self.client.patch(
            f"/api/v1/admin/usuarios/{customer.pk}/rol/",
            {"rol": Rol.ADMIN},
            format="json",
        )
        self.assertEqual(promotion.status_code, status.HTTP_200_OK)
        customer.refresh_from_db()
        self.assertEqual(customer.rol.nombre, Rol.ADMIN)

        self.client.force_authenticate(user=another_customer)
        forbidden = self.client.patch(
            f"/api/v1/admin/usuarios/{admin.pk}/rol/",
            {"rol": Rol.CLIENTE},
            format="json",
        )
        self.assertEqual(forbidden.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_cannot_demote_themselves(self):
        admin = Usuario.objects.create_user(
            email="admin@example.com",
            nombre="Admin",
            password="strong-pass-123",
            rol=self.admin_role,
        )
        self.client.force_authenticate(user=admin)

        response = self.client.patch(
            f"/api/v1/admin/usuarios/{admin.pk}/rol/",
            {"rol": Rol.CLIENTE},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        admin.refresh_from_db()
        self.assertEqual(admin.rol.nombre, Rol.ADMIN)

    @patch(
        "usuarios.views.urllib.request.urlopen",
        side_effect=urllib.error.URLError("network unavailable"),
    )
    def test_google_exchange_reports_connection_failure(self, mock_urlopen):
        response = self.client.post(
            "/api/v1/auth/google/exchange/",
            {
                "code": "authorization-code",
                "redirect_uri": "http://localhost:5173/oauth/google",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], "No se pudo conectar con Google.")
        mock_urlopen.assert_called_once()


class IdentityDataImportTests(APITestCase):
    def test_import_preserves_user_ids_password_hash_and_profile(self):
        payload = {
            "roles": [{"rol_id": 7, "nombre": Rol.CLIENTE}],
            "usuarios": [
                {
                    "usuario_id": 41,
                    "nombre": "Ana",
                    "email": "ana@example.com",
                    "password": "pbkdf2_sha256$test$hash",
                    "proveedor_auth": "local",
                    "proveedor_id": None,
                    "rol_id": 7,
                    "activo": True,
                    "fecha_registro": datetime(
                        2024, 1, 1, tzinfo=timezone.utc
                    ).isoformat(),
                    "last_login": None,
                    "is_staff": False,
                    "is_superuser": False,
                }
            ],
            "clientes": [
                {
                    "cliente_id": 51,
                    "usuario_id": 41,
                    "telefono": "3001234567",
                    "documento_tipo": "CC",
                    "documento_numero": "123",
                }
            ],
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            transfer = Path(temp_dir) / "identity.json"
            transfer.write_text(json.dumps(payload), encoding="utf-8")
            call_command(
                "import_identity_data",
                transfer,
                stdout=StringIO(),
            )

        imported = Usuario.objects.get(pk=41)
        self.assertEqual(imported.password, "pbkdf2_sha256$test$hash")
        self.assertEqual(imported.rol_id, 7)
        self.assertEqual(imported.cliente.cliente_id, 51)
        self.assertEqual(imported.cliente.telefono, "3001234567")
