from dataclasses import dataclass
import hmac

import requests
from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import APIException, AuthenticationFailed


@dataclass(frozen=True)
class RemoteUser:
    usuario_id: int
    rol_nombre: str
    is_authenticated: bool = True
    is_anonymous: bool = False


@dataclass(frozen=True)
class InternalServiceUser:
    is_authenticated: bool = True
    is_anonymous: bool = False
    is_internal_service: bool = True


class ServiceUnavailable(APIException):
    status_code = 503
    default_detail = "No fue posible validar la solicitud con el servicio requerido."
    default_code = "service_unavailable"


class CatalogServiceTokenAuthentication(BaseAuthentication):
    def authenticate_header(self, request):
        return "X-Internal-Service-Token"

    def authenticate(self, request):
        supplied_token = request.headers.get("X-Internal-Service-Token")
        if supplied_token is None:
            return None

        expected_token = settings.INTERNAL_SERVICE_TOKEN
        if not expected_token or not hmac.compare_digest(
            supplied_token, expected_token
        ):
            raise AuthenticationFailed("Credencial interna inválida.")

        return InternalServiceUser(), supplied_token


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
            raise ServiceUnavailable() from exc

        if response.status_code in (401, 403):
            raise AuthenticationFailed("Token de usuario inválido o vencido.")
        if response.status_code != 200:
            raise ServiceUnavailable()

        try:
            payload = response.json()
            user = RemoteUser(
                usuario_id=int(payload["usuario_id"]),
                rol_nombre=str(payload["rol_nombre"]),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ServiceUnavailable("Respuesta inválida del servicio de identidad.") from exc

        return user, authorization
