from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from catalogo import views


urlpatterns = [
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
