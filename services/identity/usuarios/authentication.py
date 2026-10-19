import hmac
from types import SimpleNamespace

from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed


class InternalServiceTokenAuthentication(BaseAuthentication):
    def authenticate(self, request):
        supplied = request.headers.get("X-Internal-Service-Token")
        expected = settings.INTERNAL_SERVICE_TOKEN
        if supplied is None:
            return None
        if not expected or not hmac.compare_digest(supplied, expected):
            raise AuthenticationFailed("Token de servicio interno inválido.")
        return SimpleNamespace(is_authenticated=True), supplied
