
from django.urls import path
from . import views

urlpatterns = [
    path('',                    views.MisPedidosView.as_view(),         name='mis-pedidos'),
    path('crear/',              views.CrearPedidoView.as_view(),        name='crear-pedido'),
    path('<int:pk>/',           views.DetallePedidoView.as_view(),      name='detalle-pedido'),
    path('<int:pk>/estado/',    views.CambiarEstadoPedidoView.as_view(), name='cambiar-estado'),
    path('direcciones/',        views.DireccionView.as_view(),          name='direcciones'),
]