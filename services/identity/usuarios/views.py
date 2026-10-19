from datetime import timedelta

import requests
from django.conf import settings
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Cliente, Rol, Usuario
from .permissions import EsAdmin, EsInternalService
from .serializers import (
    ActualizarClienteSerializer,
    AdminUsuarioSerializer,
    ClienteSerializer,
    LoginSerializer,
    RegistroSerializer,
    UsuarioActivoSerializer,
    UsuarioSerializer,
)


class RegistroView(generics.CreateAPIView):
    serializer_class = RegistroSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {
                "mensaje": "Cuenta creada exitosamente.",
                "usuario": UsuarioSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data)


def _google_login(idinfo):
    email = (idinfo.get("email") or "").lower()
    provider_id = idinfo.get("sub")
    name = idinfo.get("name") or idinfo.get("given_name") or email.partition("@")[0]
    if not email:
        return None, Response(
            {"detail": "No se pudo obtener el email de Google."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if not provider_id:
        return None, Response(
            {"detail": "Google no devolvió un identificador de usuario."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user = Usuario.objects.select_related("rol").filter(email=email).first()
    if user:
        if user.proveedor_auth not in ("google", "local"):
            return None, Response(
                {"detail": "Este email está asociado a otro proveedor."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not user.activo:
            return None, Response(
                {"detail": "Esta cuenta está desactivada."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if (
            user.proveedor_auth == "local"
            and not user.proveedor_id
        ) or user.proveedor_id != provider_id:
            user.proveedor_auth = "google"
            user.proveedor_id = provider_id
            user.save(update_fields=["proveedor_auth", "proveedor_id"])
    else:
        role, _ = Rol.objects.get_or_create(nombre=Rol.CLIENTE)
        user = Usuario.objects.create_user(
            email=email,
            nombre=name,
            rol=role,
            proveedor_auth="google",
            proveedor_id=provider_id,
        )
        Cliente.objects.get_or_create(usuario=user)

    refresh = RefreshToken.for_user(user)
    return {
        "usuario": UsuarioSerializer(user).data,
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    }, None


class GoogleAuthView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        credential = request.data.get("credential")
        if not credential:
            return Response(
                {"detail": "Falta el token de Google."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            idinfo = id_token.verify_oauth2_token(
                credential,
                google_requests.Request(),
                settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY,
            )
        except ValueError:
            return Response(
                {"detail": "Token de Google inválido."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        data, error = _google_login(idinfo)
        return error or Response(data)


class GoogleCodeExchangeView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        code = request.data.get("code")
        redirect_uri = request.data.get("redirect_uri")
        if not code:
            return Response(
                {"detail": "Falta el code de Google."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not redirect_uri:
            return Response(
                {"detail": "Falta redirect_uri."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        allowed = settings.GOOGLE_OAUTH_ALLOWED_REDIRECT_URIS
        if allowed and redirect_uri not in allowed:
            return Response(
                {"detail": "redirect_uri no permitido."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            token_response = requests.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY,
                    "client_secret": settings.SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code",
                },
                timeout=10,
            )
        except requests.RequestException:
            return Response(
                {"detail": "No se pudo conectar con Google."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            token_data = token_response.json()
        except ValueError:
            token_data = {}
        if token_response.status_code >= 400:
            message = (
                token_data.get("error_description")
                or token_data.get("error")
                or "Error intercambiando code."
            )
            return Response(
                {"detail": message},
                status=status.HTTP_400_BAD_REQUEST,
            )
        credential = token_data.get("id_token")
        if not credential:
            return Response(
                {"detail": "Google no devolvió id_token."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            idinfo = id_token.verify_oauth2_token(
                credential,
                google_requests.Request(),
                settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY,
            )
        except ValueError:
            return Response(
                {"detail": "Token de Google inválido."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        data, error = _google_login(idinfo)
        return error or Response(data)


class PerfilView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "GET":
            return ClienteSerializer
        return ActualizarClienteSerializer

    def get_object(self):
        return get_object_or_404(Cliente, usuario=self.request.user)


class MiUsuarioView(generics.RetrieveAPIView):
    serializer_class = UsuarioSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class AdminUsuariosView(APIView):
    permission_classes = [IsAuthenticated, EsAdmin]

    def get(self, request):
        users = Usuario.objects.select_related("rol").all().order_by("-fecha_registro")
        search = request.query_params.get("search", "").strip()
        role = request.query_params.get("rol", "").strip()
        if search:
            users = users.filter(Q(nombre__icontains=search) | Q(email__icontains=search))
        if role in (Rol.ADMIN, Rol.CLIENTE):
            users = users.filter(rol__nombre=role)

        stats = {
            "total": users.count(),
            "activos": users.filter(activo=True).count(),
            "admins": users.filter(rol__nombre=Rol.ADMIN).count(),
            "clientes": users.filter(rol__nombre=Rol.CLIENTE).count(),
        }
        paginator = PageNumberPagination()
        page = paginator.paginate_queryset(users, request)
        return Response(
            {
                "usuarios": AdminUsuarioSerializer(page, many=True).data,
                "stats": stats,
                "pages": paginator.page.paginator.num_pages if paginator.page else 1,
                "total": users.count(),
            }
        )


class AdminUsuarioActivoView(APIView):
    permission_classes = [IsAuthenticated, EsAdmin]

    def patch(self, request, usuario_id):
        user = Usuario.objects.select_related("rol").filter(usuario_id=usuario_id).first()
        if not user:
            return Response(
                {"detail": "Usuario no encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )
        if user.rol.nombre == Rol.ADMIN:
            return Response(
                {"detail": "No se puede desactivar un admin."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = UsuarioActivoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user.activo = serializer.validated_data["activo"]
        user.save(update_fields=["activo"])
        return Response({"usuario_id": user.usuario_id, "activo": user.activo})


@api_view(["GET"])
@permission_classes([EsInternalService])
def internal_summary(request):
    now = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    next_month = (month_start + timedelta(days=32)).replace(day=1)
    previous_month = (month_start - timedelta(days=1)).replace(day=1)
    customers = Usuario.objects.filter(rol__nombre=Rol.CLIENTE)
    return Response(
        {
            "total_clientes": customers.count(),
            "clientes_mes": customers.filter(
                fecha_registro__gte=month_start,
                fecha_registro__lt=next_month,
            ).count(),
            "clientes_mes_anterior": customers.filter(
                fecha_registro__gte=previous_month,
                fecha_registro__lt=month_start,
            ).count(),
        }
    )
