from rest_framework.permissions import BasePermission


class EsServicioInterno(BasePermission):
    def has_permission(self, request, view):
        return getattr(request.user, "is_internal_service", False)
