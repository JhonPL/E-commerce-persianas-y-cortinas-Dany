from types import SimpleNamespace

import requests
from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import APIException, AuthenticationFailed


class IdentityServiceUnavailable(APIException):
    status_code = 503
    default_detail = "El servicio de identidad no está disponible."
    default_code = "identity_service_unavailable"


class RemoteIdentityUser:
    is_authenticated = True

    def __init__(self, data):
        self.usuario_id = data["usuario_id"]
        self.id = self.usuario_id
        self.nombre = data["nombre"]
        self.email = data["email"]
        self.rol = SimpleNamespace(nombre=data["rol_nombre"])
        self.is_staff = self.rol.nombre == "admin"


class RemoteIdentityAuthentication(BaseAuthentication):
    def authenticate(self, request):
        authorization = request.headers.get("Authorization")
        if not authorization:
            return None
        endpoint = settings.IDENTITY_SERVICE_URL.rstrip("/") + "/api/v1/auth/me/"
        try:
            response = requests.get(
                endpoint,
                headers={"Authorization": authorization},
                timeout=settings.IDENTITY_SERVICE_TIMEOUT_SECONDS,
            )
        except requests.RequestException as exc:
            raise IdentityServiceUnavailable() from exc
        if response.status_code in (401, 403):
            raise AuthenticationFailed("Token inválido o cuenta desactivada.")
        if response.status_code != 200:
            raise IdentityServiceUnavailable(
                "El servicio de identidad no pudo validar el token."
            )
        try:
            data = response.json()
            user = RemoteIdentityUser(data)
        except (ValueError, KeyError, TypeError) as exc:
            raise IdentityServiceUnavailable(
                "El servicio de identidad devolvió una respuesta inválida."
            ) from exc
        return user, authorization


def get_identity_dashboard():
    if not settings.INTERNAL_SERVICE_TOKEN:
        raise IdentityServiceUnavailable(
            "Falta configurar INTERNAL_SERVICE_TOKEN para consultar identidad."
        )
    endpoint = (
        settings.IDENTITY_SERVICE_URL.rstrip("/")
        + "/api/internal/identity/resumen/"
    )
    try:
        response = requests.get(
            endpoint,
            headers={
                "X-Internal-Service-Token": settings.INTERNAL_SERVICE_TOKEN,
            },
            timeout=settings.IDENTITY_SERVICE_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as exc:
        raise IdentityServiceUnavailable() from exc
    except ValueError as exc:
        raise IdentityServiceUnavailable(
            "El servicio de identidad devolvió una respuesta inválida."
        ) from exc

    required = {"total_clientes", "clientes_mes", "clientes_mes_anterior"}
    if not isinstance(data, dict) or not required.issubset(data):
        raise IdentityServiceUnavailable(
            "El servicio de identidad devolvió una respuesta incompleta."
        )
    return data
