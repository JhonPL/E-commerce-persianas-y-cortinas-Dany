from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from facturacion.views import (
    DemoInvoicePdfView,
    FacturaDetailView,
    FacturaListCreateView,
)


urlpatterns = [
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
