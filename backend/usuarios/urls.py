from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    path('registro/',       views.RegistroView.as_view(),   name='registro'),
    path('login/',          views.LoginView.as_view(),      name='login'),
    path('token/refresh/',  TokenRefreshView.as_view(),     name='token_refresh'),
    path('perfil/',         views.PerfilView.as_view(),     name='perfil'),
    path('me/',             views.MiUsuarioView.as_view(),  name='me'),
]