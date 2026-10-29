from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from simulador.health import live as health_live
from simulador.health import ready as health_ready
from simulador.views import SimulatePaymentView


urlpatterns = [
    path("health/live/", health_live),
    path("health/ready/", health_ready),
    path(
        "api/v1/payments/simulate/",
        SimulatePaymentView.as_view(),
        name="simulate-payment",
    ),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
]