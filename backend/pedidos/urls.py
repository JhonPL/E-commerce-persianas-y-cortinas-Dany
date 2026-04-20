
from django.urls import path
from . import views

urlpatterns = [
    path('',                        views.mis_pedidos,                      name='mis-pedidos'),
    path('<int:pedido_id>/',        views.detalle_pedido,                   name='detalle-pedido'),
]