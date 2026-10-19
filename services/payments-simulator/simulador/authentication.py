from dataclasses import dataclass

import requests
from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import APIException, AuthenticationFailed


@dataclass(frozen=True)
class RemoteUser:
    usuario_id: int
    nombre: str = ""
    email: str = ""
    rol_nombre: str = ""
    is_authenticated: bool = True
    is_anonymous: bool = False


class IdentityServiceUnavailable(APIException):
    status_code = 503
    default_detail = "No fue posible validar la sesión con el servicio de identidad."
    default_code = "identity_service_unavailable"


class RemoteUserAuthentication(BaseAuthentication):
    def authenticate(self, request):
        authorization = request.headers.get("Authorization")
        if not authorization:
            return None

        try:
            response = requests.get(
                settings.AUTH_SERVICE_URL,
                headers={"Authorization": authorization},
                timeout=settings.SERVICE_TIMEOUT_SECONDS,
            )
        except requests.RequestException as exc:
            raise IdentityServiceUnavailable() from exc

        if response.status_code in (401, 403):
            raise AuthenticationFailed("Token de usuario inválido o vencido.")
        if response.status_code != 200:
            raise IdentityServiceUnavailable()

        try:
            payload = response.json()
            user = RemoteUser(
                usuario_id=int(payload["usuario_id"]),
                nombre=str(payload.get("nombre", "")),
                email=str(payload.get("email", "")),
                rol_nombre=str(payload.get("rol_nombre", "")),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise IdentityServiceUnavailable(
                "Respuesta inválida del servicio de identidad."
            ) from exc

        return user, authorization