from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from facturacion.health import live as health_live
from facturacion.health import ready as health_ready
from facturacion.views import (
    DemoInvoicePdfView,
    FacturaDetailView,
    FacturaListCreateView,
)


urlpatterns = [
    path("health/live/", health_live),
    path("health/ready/", health_ready),
    path("api/internal/facturas/", FacturaListCreateView.as_view()),
    path("api/internal/facturas/demo-pdf/", DemoInvoicePdfView.as_view()),
    path(
        "api/internal/facturas/pedido/<int:pedido_id>/",
        FacturaDetailView.as_view(),
    ),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
]
