from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from notificaciones.views import PedidoApprovedNotificationView


urlpatterns = [
    path(
        "api/internal/notificaciones/pedidos/",
        PedidoApprovedNotificationView.as_view(),
        name="notify-approved-order",
    ),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
]
