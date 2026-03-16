from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),

    path('api/v1/auth/',         include('usuarios.urls')),
    path('api/v1/catalogo/',     include('catalogo.urls')),
    path('api/v1/carrito/',      include('carrito.urls')),
    path('api/v1/pedidos/',      include('pedidos.urls')),
    path('api/v1/pagos/',        include('pagos.urls')),

    # Documentación automática
    path('api/schema/',   SpectacularAPIView.as_view(),        name='schema'),
    path('api/docs/',     SpectacularSwaggerView.as_view(
                              url_name='schema'), name='swagger-ui'),
]