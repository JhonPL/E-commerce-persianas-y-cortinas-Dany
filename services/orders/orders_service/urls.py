from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from pedidos import views
from pedidos.health import live as health_live
from pedidos.health import ready as health_ready


urlpatterns = [
    path("health/live/", health_live),
    path("health/ready/", health_ready),
    path("api/v1/pedidos/checkout/", views.checkout),
    path("api/v1/pedidos/", views.mis_pedidos),
    path(
        "api/v1/pedidos/<int:pedido_id>/factura/",
        views.descargar_factura,
    ),
    path("api/v1/pedidos/<int:pedido_id>/", views.detalle_pedido),
    path("api/v1/admin/pedidos/", views.admin_pedidos_list),
    path(
        "api/v1/admin/pedidos/<int:pedido_id>/",
        views.admin_detalle_pedido,
    ),
    path(
        "api/v1/admin/pedidos/<int:pedido_id>/estado/",
        views.admin_pedido_cambiar_estado,
    ),
    path("api/v1/admin/estados-pedido/", views.admin_estados_list),
    path(
        "api/internal/pedidos/productos/<int:product_id>/",
        views.check_product_references,
    ),
    path(
        "api/internal/pedidos/<int:pedido_id>/payment-context/",
        views.internal_payment_context,
    ),
    path(
        "api/internal/pedidos/<int:pedido_id>/payment-result/",
        views.internal_payment_result,
    ),
    path(
        "api/internal/pedidos/expire-unpaid-orders/",
        views.expire_unpaid_orders_scheduled,
        name="expire-unpaid-orders-scheduled",
    ),
    path("api/internal/pedidos/dashboard/", views.internal_dashboard),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
]
