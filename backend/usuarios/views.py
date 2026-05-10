from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
import requests
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from .models import Usuario, Cliente, Rol
from .serializers import (RegistroSerializer, LoginSerializer,
                           UsuarioSerializer, ClienteSerializer,
                           ActualizarClienteSerializer)


class RegistroView(generics.CreateAPIView):
    serializer_class = RegistroSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {'mensaje': 'Cuenta creada exitosamente.',
             'usuario': UsuarioSerializer(user).data},
            status=status.HTTP_201_CREATED
        )


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data,
                                     context={'request': request})
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)

class GoogleAuthView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        credential = request.data.get('credential')
        if not credential:
            return Response({'detail': 'Falta el token de Google.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            idinfo = id_token.verify_oauth2_token(
                credential,
                google_requests.Request(),
                settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY,
            )
        except ValueError:
            return Response({'detail': 'Token de Google inválido.'}, status=status.HTTP_400_BAD_REQUEST)

        email = idinfo.get('email')
        sub = idinfo.get('sub')
        nombre = idinfo.get('name') or idinfo.get('given_name') or (email.split('@')[0] if email else '')

        if not email:
            return Response({'detail': 'No se pudo obtener el email de Google.'}, status=status.HTTP_400_BAD_REQUEST)

        user = Usuario.objects.filter(email=email).first()
        if user:
            if user.proveedor_auth not in ['google', 'local']:
                return Response({'detail': 'Este email está asociado a otro proveedor.'}, status=status.HTTP_400_BAD_REQUEST)
            if not user.activo:
                return Response({'detail': 'Esta cuenta está desactivada.'}, status=status.HTTP_400_BAD_REQUEST)
            if user.proveedor_auth == 'local' and not user.proveedor_id:
                user.proveedor_auth = 'google'
                user.proveedor_id = sub
                user.save(update_fields=['proveedor_auth', 'proveedor_id'])
            elif user.proveedor_auth == 'google' and user.proveedor_id != sub:
                user.proveedor_id = sub
                user.save(update_fields=['proveedor_id'])
        else:
            rol, _ = Rol.objects.get_or_create(nombre=Rol.CLIENTE)
            user = Usuario.objects.create_user(
                email=email,
                nombre=nombre,
                password=None,
                rol=rol,
                proveedor_auth='google',
                proveedor_id=sub,
            )
            Cliente.objects.get_or_create(usuario=user)

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                'usuario': UsuarioSerializer(user).data,
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            },
            status=status.HTTP_200_OK,
        )

class GoogleCodeExchangeView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        code = request.data.get('code')
        redirect_uri = request.data.get('redirect_uri')

        if not code:
            return Response({'detail': 'Falta el code de Google.'}, status=status.HTTP_400_BAD_REQUEST)
        if not redirect_uri:
            return Response({'detail': 'Falta redirect_uri.'}, status=status.HTTP_400_BAD_REQUEST)

        allowed = getattr(settings, 'GOOGLE_OAUTH_ALLOWED_REDIRECT_URIS', [])
        if allowed and redirect_uri not in allowed:
            return Response({'detail': 'redirect_uri no permitido.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            token_res = requests.post(
                'https://oauth2.googleapis.com/token',
                data={
                    'code': code,
                    'client_id': settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY,
                    'client_secret': settings.SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET,
                    'redirect_uri': redirect_uri,
                    'grant_type': 'authorization_code',
                },
                timeout=10,
            )
        except requests.RequestException:
            return Response({'detail': 'No se pudo conectar con Google.'}, status=status.HTTP_400_BAD_REQUEST)

        token_data = {}
        try:
            token_data = token_res.json()
        except ValueError:
            token_data = {}

        if token_res.status_code >= 400:
            msg = token_data.get('error_description') or token_data.get('error') or 'Error intercambiando code.'
            return Response({'detail': msg}, status=status.HTTP_400_BAD_REQUEST)

        credential = token_data.get('id_token')
        if not credential:
            return Response({'detail': 'Google no devolvió id_token.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            idinfo = id_token.verify_oauth2_token(
                credential,
                google_requests.Request(),
                settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY,
            )
        except ValueError:
            return Response({'detail': 'Token de Google inválido.'}, status=status.HTTP_400_BAD_REQUEST)

        email = idinfo.get('email')
        sub = idinfo.get('sub')
        nombre = idinfo.get('name') or idinfo.get('given_name') or (email.split('@')[0] if email else '')

        if not email:
            return Response({'detail': 'No se pudo obtener el email de Google.'}, status=status.HTTP_400_BAD_REQUEST)

        user = Usuario.objects.filter(email=email).first()
        if user:
            if user.proveedor_auth not in ['google', 'local']:
                return Response({'detail': 'Este email está asociado a otro proveedor.'}, status=status.HTTP_400_BAD_REQUEST)
            if not user.activo:
                return Response({'detail': 'Esta cuenta está desactivada.'}, status=status.HTTP_400_BAD_REQUEST)
            if user.proveedor_auth == 'local' and not user.proveedor_id:
                user.proveedor_auth = 'google'
                user.proveedor_id = sub
                user.save(update_fields=['proveedor_auth', 'proveedor_id'])
            elif user.proveedor_auth == 'google' and user.proveedor_id != sub:
                user.proveedor_id = sub
                user.save(update_fields=['proveedor_id'])
        else:
            rol, _ = Rol.objects.get_or_create(nombre=Rol.CLIENTE)
            user = Usuario.objects.create_user(
                email=email,
                nombre=nombre,
                password=None,
                rol=rol,
                proveedor_auth='google',
                proveedor_id=sub,
            )
            Cliente.objects.get_or_create(usuario=user)

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                'usuario': UsuarioSerializer(user).data,
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            },
            status=status.HTTP_200_OK,
        )
class PerfilView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return ClienteSerializer
        return ActualizarClienteSerializer

    def get_object(self):
        return self.request.user.cliente


class MiUsuarioView(generics.RetrieveAPIView):
    serializer_class   = UsuarioSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


