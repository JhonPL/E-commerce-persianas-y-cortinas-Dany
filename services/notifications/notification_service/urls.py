from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from notificaciones.views import (
    ContactMessageNotificationView,
    PedidoApprovedNotificationView,
    PedidoStatusChangedNotificationView,
    email_logo,
)
from notificaciones.health import live as health_live
from notificaciones.health import ready as health_ready


urlpatterns = [
    path("health/live/", health_live),
    path("health/ready/", health_ready),
    path("email-assets/logogreen.png", email_logo),
    path(
        "api/internal/notificaciones/pedidos/",
        PedidoApprovedNotificationView.as_view(),
        name="notify-approved-order",
    ),
    path(
        "api/internal/notificaciones/pedidos/estado/",
        PedidoStatusChangedNotificationView.as_view(),
        name="notify-order-status-changed",
    ),
    path(
        "api/internal/notificaciones/contacto/",
        ContactMessageNotificationView.as_view(),
        name="notify-contact-message",
    ),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
]
