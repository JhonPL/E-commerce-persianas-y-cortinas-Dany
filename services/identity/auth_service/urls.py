from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework_simplejwt.views import TokenRefreshView

from usuarios import views


urlpatterns = [
    path("api/v1/auth/registro/", views.RegistroView.as_view()),
    path("api/v1/auth/login/", views.LoginView.as_view()),
    path("api/v1/auth/google/", views.GoogleAuthView.as_view()),
    path("api/v1/auth/google/exchange/", views.GoogleCodeExchangeView.as_view()),
    path("api/v1/auth/token/refresh/", TokenRefreshView.as_view()),
    path("api/v1/auth/perfil/", views.PerfilView.as_view()),
    path("api/v1/auth/me/", views.MiUsuarioView.as_view()),
    path("api/v1/admin/usuarios/", views.AdminUsuariosView.as_view()),
    path(
        "api/v1/admin/usuarios/<int:usuario_id>/activo/",
        views.AdminUsuarioActivoView.as_view(),
    ),
    path(
        "api/v1/admin/usuarios/<int:usuario_id>/rol/",
        views.AdminUsuarioRolView.as_view(),
    ),
    path("api/internal/identity/resumen/", views.internal_summary),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
]
