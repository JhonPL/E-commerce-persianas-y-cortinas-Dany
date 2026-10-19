from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from simulador.views import SimulatePaymentView


urlpatterns = [
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