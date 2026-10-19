import hmac
from dataclasses import dataclass

from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed


@dataclass(frozen=True)
class InternalServiceUser:
    is_authenticated: bool = True
    is_anonymous: bool = False
    is_internal_service: bool = True


class InternalServiceTokenAuthentication(BaseAuthentication):
    def authenticate_header(self, request):
        return "X-Internal-Service-Token"

    def authenticate(self, request):
        supplied = request.headers.get("X-Internal-Service-Token")
        if supplied is None:
            return None
        expected = settings.INTERNAL_SERVICE_TOKEN
        if not expected or not hmac.compare_digest(supplied, expected):
            raise AuthenticationFailed("Credencial interna inválida.")
        return InternalServiceUser(), supplied
