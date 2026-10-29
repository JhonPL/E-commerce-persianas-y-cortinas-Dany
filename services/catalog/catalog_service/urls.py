from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from catalogo import views
from catalogo.health import live as health_live
from catalogo.health import ready as health_ready


urlpatterns = [
    path("health/live/", health_live),
    path("health/ready/", health_ready),
    path("api/v1/catalogo/", include("catalogo.urls")),
    path("api/internal/catalogo/productos/", views.internal_products),
    path("api/internal/catalogo/resumen/", views.internal_summary),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
]
