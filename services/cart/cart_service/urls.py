from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from carrito.views import delete_product_references


urlpatterns = [
    path("api/v1/carrito/", include("carrito.urls")),
    path(
        "api/internal/carrito/productos/<int:product_id>/",
        delete_product_references,
        name="internal-cart-product-references",
    ),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
]
