from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from catalog_service_proxy import CatalogServiceProxy
from cart_service_proxy import CartServiceProxy
from identity_service_proxy import IdentityServiceProxy
from orders_service_proxy import OrdersServiceProxy
from payments_service_proxy import PaymentsServiceProxy
from integrations.views import prepare_product_deletion
from pedidos.views import admin_dashboard

urlpatterns = [
    path('admin/', admin.site.urls),

    path(
        'api/v1/auth/',
        IdentityServiceProxy.as_view(),
        {'prefixes': ('api', 'v1', 'auth')},
    ),
    path(
        'api/v1/auth/<path:subpath>/',
        IdentityServiceProxy.as_view(),
        {'prefixes': ('api', 'v1', 'auth')},
    ),
    path(
        'api/v1/admin/usuarios/',
        IdentityServiceProxy.as_view(),
        {'prefixes': ('api', 'v1', 'admin', 'usuarios')},
    ),
    path(
        'api/v1/admin/usuarios/<path:subpath>/',
        IdentityServiceProxy.as_view(),
        {'prefixes': ('api', 'v1', 'admin', 'usuarios')},
    ),
    path('api/v1/catalogo/', CatalogServiceProxy.as_view(), {'subpath': ''}),
    path('api/v1/catalogo/<path:subpath>/', CatalogServiceProxy.as_view()),
    path('api/v1/carrito/', CartServiceProxy.as_view(), {'subpath': ''}),
    path('api/v1/carrito/<path:subpath>/', CartServiceProxy.as_view()),
    path(
        'api/v1/pedidos/',
        OrdersServiceProxy.as_view(),
        {'prefixes': ('api', 'v1', 'pedidos')},
    ),
    path(
        'api/v1/pedidos/<path:subpath>/',
        OrdersServiceProxy.as_view(),
        {'prefixes': ('api', 'v1', 'pedidos')},
    ),
    path(
        'api/v1/admin/pedidos/',
        OrdersServiceProxy.as_view(),
        {'prefixes': ('api', 'v1', 'admin', 'pedidos')},
    ),
    path(
        'api/v1/admin/pedidos/<path:subpath>/',
        OrdersServiceProxy.as_view(),
        {'prefixes': ('api', 'v1', 'admin', 'pedidos')},
    ),
    path(
        'api/v1/admin/estados-pedido/',
        OrdersServiceProxy.as_view(),
        {'subpath': 'api/v1/admin/estados-pedido'},
    ),
    path(
        'api/v1/payments/',
        PaymentsServiceProxy.as_view(),
        {'subpath': ''},
    ),
    path(
        'api/v1/payments/<path:subpath>/',
        PaymentsServiceProxy.as_view(),
    ),
    path('api/v1/admin/dashboard/', admin_dashboard, name='admin_dashboard'),
    path('api/v1/pagos/',        include('pagos.urls')),
    path(
        'api/internal/catalogo/productos/<int:product_id>/',
        prepare_product_deletion,
        name='internal-catalog-product-deletion',
    ),

    # Documentación automática
    path('api/schema/',   SpectacularAPIView.as_view(),        name='schema'),
    path('api/docs/',     SpectacularSwaggerView.as_view(
                              url_name='schema'), name='swagger-ui'),
]