from django.urls import path
from . import views

urlpatterns = [
    path('pedidos/', views.admin_pedidos_list, name='admin_pedidos_list'),
    path('pedidos/<int:pedido_id>/estado/', views.admin_pedido_cambiar_estado, name='admin_pedido_estado'),
    path('estados-pedido/', views.admin_estados_list, name='admin_estados_list'),
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
]
