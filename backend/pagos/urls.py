from django.urls import path
from . import views

urlpatterns = [
    path('iniciar/',  views.IniciarPagoView.as_view(),   name='iniciar-pago'),
    path('webhook/',  views.WompiWebhookView.as_view(),  name='wompi-webhook'),
]