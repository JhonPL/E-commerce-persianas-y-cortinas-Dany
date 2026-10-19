import hmac

from django.conf import settings
from rest_framework.permissions import BasePermission


class EsAdmin(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and getattr(getattr(request.user, "rol", None), "nombre", None) == "admin"
        )


class EsInternalService(BasePermission):
    def has_permission(self, request, view):
        token = settings.INTERNAL_SERVICE_TOKEN
        supplied = request.auth
        return bool(
            token
            and isinstance(supplied, str)
            and hmac.compare_digest(supplied, token)
        )
