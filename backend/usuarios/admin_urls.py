from django.urls import path
from . import views

urlpatterns = [
    path('usuarios/', views.AdminUsuariosView.as_view(), name='admin_usuarios'),
    path('usuarios/<int:usuario_id>/activo/', views.AdminUsuarioActivoView.as_view(), name='admin_usuario_activo'),
]
