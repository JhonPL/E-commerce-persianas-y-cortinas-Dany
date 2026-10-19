from rest_framework.permissions import BasePermission


class IsCatalogAdmin(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and getattr(request.user, "rol_nombre", None) == "admin"
        )


class IsCatalogService(BasePermission):
    def has_permission(self, request, view):
        return getattr(request.user, "is_internal_service", False) is True
