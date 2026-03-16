from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from .models import Categoria, Producto, ImagenProducto
from .serializers import (CategoriaSerializer, ProductoListSerializer,
                           ProductoDetalleSerializer, ProductoAdminSerializer,
                           ImagenProductoSerializer)
from usuarios.permissions import EsAdmin
import cloudinary.uploader


class CategoriaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset           = Categoria.objects.filter(activo=True)
    serializer_class   = CategoriaSerializer
    permission_classes = [AllowAny]


class ProductoViewSet(viewsets.ModelViewSet):
    queryset       = Producto.objects.filter(activo=True)\
                             .select_related('categoria')\
                             .prefetch_related('imagenes')
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields   = ['nombre', 'descripcion']
    ordering_fields = ['precio_m2', 'fecha_creacion']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [EsAdmin()]

    def get_serializer_class(self):
        if self.action == 'list':
            return ProductoListSerializer
        if self.action in ['create', 'update', 'partial_update']:
            return ProductoAdminSerializer
        return ProductoDetalleSerializer

    @action(detail=True, methods=['post'], permission_classes=[EsAdmin])
    def subir_imagen(self, request, pk=None):
        producto = self.get_object()
        archivo  = request.FILES.get('imagen')
        if not archivo:
            return Response({'error': 'No se envió imagen.'}, status=400)
        resultado = cloudinary.uploader.upload(archivo,
                                               folder=f'productos/{producto.pk}')
        imagen = ImagenProducto.objects.create(
            producto     = producto,
            url          = resultado['secure_url'],
            es_principal = not producto.imagenes.exists(),
        )
        return Response(ImagenProductoSerializer(imagen).data,
                        status=status.HTTP_201_CREATED)