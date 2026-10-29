from django.http import JsonResponse
from django.urls import path

from gateway.views import (
    admin_dashboard,
    contact_notification,
    delete_catalog_product,
    prepare_product_deletion,
)
from gateway.proxies import (
    CartServiceProxy,
    CatalogServiceProxy,
    IdentityServiceProxy,
    OrdersServiceProxy,
    PaymentsServiceProxy,
)
from gateway.health import live as health_live
from gateway.health import ready as health_ready


def health(request):
    return JsonResponse({"status": "ok", "service": "gateway"})


def catalog_product(request, product_id):
    if request.method == "DELETE":
        return delete_catalog_product(request, product_id)
    return CatalogServiceProxy.as_view()(
        request,
        subpath=f"productos/{product_id}",
    )


urlpatterns = [
    path("health/", health),
    path("health/live/", health_live),
    path("health/ready/", health_ready),
    path("api/v1/contacto/", contact_notification),
    path(
        "api/v1/auth/",
        IdentityServiceProxy.as_view(),
        {"prefixes": ("api", "v1", "auth")},
    ),
    path(
        "api/v1/auth/<path:subpath>/",
        IdentityServiceProxy.as_view(),
        {"prefixes": ("api", "v1", "auth")},
    ),
    path(
        "api/v1/admin/usuarios/",
        IdentityServiceProxy.as_view(),
        {"prefixes": ("api", "v1", "admin", "usuarios")},
    ),
    path(
        "api/v1/admin/usuarios/<path:subpath>/",
        IdentityServiceProxy.as_view(),
        {"prefixes": ("api", "v1", "admin", "usuarios")},
    ),
    path(
        "api/v1/catalogo/productos/<int:product_id>/",
        catalog_product,
    ),
    path("api/v1/catalogo/", CatalogServiceProxy.as_view(), {"subpath": ""}),
    path("api/v1/catalogo/<path:subpath>/", CatalogServiceProxy.as_view()),
    path("api/v1/carrito/", CartServiceProxy.as_view(), {"subpath": ""}),
    path("api/v1/carrito/<path:subpath>/", CartServiceProxy.as_view()),
    path(
        "api/v1/pedidos/",
        OrdersServiceProxy.as_view(),
        {"prefixes": ("api", "v1", "pedidos")},
    ),
    path(
        "api/v1/pedidos/<path:subpath>/",
        OrdersServiceProxy.as_view(),
        {"prefixes": ("api", "v1", "pedidos")},
    ),
    path(
        "api/v1/admin/pedidos/",
        OrdersServiceProxy.as_view(),
        {"prefixes": ("api", "v1", "admin", "pedidos")},
    ),
    path(
        "api/v1/admin/pedidos/<path:subpath>/",
        OrdersServiceProxy.as_view(),
        {"prefixes": ("api", "v1", "admin", "pedidos")},
    ),
    path(
        "api/v1/admin/estados-pedido/",
        OrdersServiceProxy.as_view(),
        {"subpath": "api/v1/admin/estados-pedido"},
    ),
    path("api/v1/admin/dashboard/", admin_dashboard),
    path("api/v1/payments/", PaymentsServiceProxy.as_view(), {"subpath": ""}),
    path(
        "api/v1/payments/<path:subpath>/",
        PaymentsServiceProxy.as_view(),
    ),
    path(
        "api/internal/catalogo/productos/<int:product_id>/",
        prepare_product_deletion,
    ),
]