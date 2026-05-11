from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .models import Categoria, Producto, ImagenProducto
from .serializers import (CategoriaSerializer, ProductoListSerializer,
                           ProductoDetalleSerializer, ProductoAdminSerializer,
                           ImagenProductoSerializer)
from usuarios.permissions import EsAdmin
import cloudinary.uploader


class CategoriaViewSet(viewsets.ModelViewSet):
    serializer_class = CategoriaSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [EsAdmin()]

    def get_queryset(self):
        qs = Categoria.objects.all()
        # Tienda pública solo ve activas; admin ve todas
        user = self.request.user
        if user.is_anonymous or (hasattr(user, 'rol') and user.rol.nombre != 'admin'):
            qs = qs.filter(activo=True)
        return qs


class ProductoViewSet(viewsets.ModelViewSet):
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields   = ['nombre', 'descripcion']
    ordering_fields = ['precio_m2', 'fecha_creacion']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [EsAdmin()]

    def get_queryset(self):
        user = self.request.user
        qs   = Producto.objects.select_related('categoria').prefetch_related('imagenes')
        # Tienda pública solo ve activos; admin ve todos
        if user.is_anonymous or (hasattr(user, 'rol') and user.rol.nombre != 'admin'):
            qs = qs.filter(activo=True)
        return qs

    def get_serializer_class(self):
        if self.action == 'list':
            return ProductoListSerializer
        if self.action in ['create', 'update', 'partial_update']:
            return ProductoAdminSerializer
        return ProductoDetalleSerializer

    @action(detail=True, methods=['post'], permission_classes=[EsAdmin])
    def subir_imagen(self, request, pk=None):
        producto     = self.get_object()
        url          = request.data.get('url')
        es_principal = request.data.get('es_principal', False)

        if not url:
            # Si no viene URL intentar subir archivo multipart
            archivo = request.FILES.get('imagen')
            if not archivo:
                return Response({'error': 'Se requiere url o imagen.'}, status=400)
            resultado    = cloudinary.uploader.upload(
                archivo, folder=f'cortinas-dany/productos/{producto.pk}'
            )
            url          = resultado['secure_url']
            es_principal = not producto.imagenes.exists()

        # Si es principal, quitar el flag de las demás
        if es_principal:
            producto.imagenes.update(es_principal=False)

        imagen = ImagenProducto.objects.create(
            producto     = producto,
            url          = url,
            es_principal = es_principal,
            orden        = producto.imagenes.count(),
        )
        return Response(ImagenProductoSerializer(imagen).data,
                        status=status.HTTP_201_CREATED)