from django.urls import path
from . import views

urlpatterns = [
    path('',            views.CarritoView.as_view(),        name='carrito'),
    path('<int:pk>/',   views.CarritoItemView.as_view(),    name='carrito-item'),
    path('limpiar/',    views.LimpiarCarritoView.as_view(), name='carrito-limpiar'),
]