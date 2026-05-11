from rest_framework.permissions import BasePermission


class EsAdmin(BasePermission):
    """Solo administradores"""
    def has_permission(self, request, view):
        return (request.user.is_authenticated and
                request.user.rol.nombre == 'admin')


class EsCliente(BasePermission):
    """Solo clientes registrados"""
    def has_permission(self, request, view):
        return (request.user.is_authenticated and
                request.user.rol.nombre == 'cliente')


class EsPropietario(BasePermission):
    """Solo el dueño del objeto"""
    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'usuario'):
            return obj.usuario == request.user
        if hasattr(obj, 'cliente'):
            return obj.cliente.usuario == request.user
        return False