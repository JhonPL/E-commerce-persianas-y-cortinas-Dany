import cloudinary.uploader
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action, api_view, authentication_classes, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .authentication import CatalogServiceTokenAuthentication
from .models import Categoria, ImagenProducto, Producto
from .permissions import IsCatalogAdmin, IsCatalogService
from .serializers import (
    CategoriaSerializer,
    ImagenProductoSerializer,
    ProductoAdminSerializer,
    ProductoDetalleSerializer,
    ProductoListSerializer,
)


class CategoriaViewSet(viewsets.ModelViewSet):
    serializer_class = CategoriaSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]
        return [IsCatalogAdmin()]

    def get_queryset(self):
        queryset = Categoria.objects.all()
        user = self.request.user
        if not (
            getattr(user, "is_authenticated", False)
            and getattr(user, "rol_nombre", None) == "admin"
        ):
            queryset = queryset.filter(activo=True)
        return queryset.order_by("categoria_id")


class ProductoViewSet(viewsets.ModelViewSet):
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["nombre", "descripcion"]
    ordering_fields = ["precio_m2", "fecha_creacion"]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]
        return [IsCatalogAdmin()]

    def get_queryset(self):
        queryset = (
            Producto.objects.select_related("categoria")
            .prefetch_related("imagenes")
        )
        user = self.request.user
        if not (
            getattr(user, "is_authenticated", False)
            and getattr(user, "rol_nombre", None) == "admin"
        ):
            queryset = queryset.filter(activo=True)
        return queryset.order_by("producto_id")

    def get_serializer_class(self):
        if self.action == "list":
            return ProductoListSerializer
        if self.action in ["create", "update", "partial_update"]:
            return ProductoAdminSerializer
        return ProductoDetalleSerializer

    @action(detail=True, methods=["post"], permission_classes=[IsCatalogAdmin])
    def subir_imagen(self, request, pk=None):
        producto = self.get_object()
        url = request.data.get("url")
        es_principal = request.data.get("es_principal", False)

        if not url:
            archivo = request.FILES.get("imagen")
            if not archivo:
                return Response(
                    {"error": "Se requiere url o imagen."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            resultado = cloudinary.uploader.upload(
                archivo, folder=f"cortinas-dany/productos/{producto.pk}"
            )
            url = resultado["secure_url"]
            es_principal = not producto.imagenes.exists()

        if es_principal:
            producto.imagenes.update(es_principal=False)

        imagen = ImagenProducto.objects.create(
            producto=producto,
            url=url,
            es_principal=es_principal,
            orden=producto.imagenes.count(),
        )
        return Response(
            ImagenProductoSerializer(imagen).data,
            status=status.HTTP_201_CREATED,
        )

    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


@api_view(["GET"])
@authentication_classes([CatalogServiceTokenAuthentication])
@permission_classes([IsCatalogService])
def internal_products(request):
    raw_ids = request.query_params.get("ids", "")
    if not raw_ids:
        raise ValidationError({"ids": "Se requiere al menos un identificador."})

    try:
        product_ids = {int(value) for value in raw_ids.split(",")}
    except ValueError as exc:
        raise ValidationError({"ids": "Los identificadores deben ser enteros."}) from exc

    if not product_ids or min(product_ids) < 1:
        raise ValidationError({"ids": "Los identificadores deben ser positivos."})

    products = (
        Producto.objects.filter(producto_id__in=product_ids)
        .select_related("categoria")
        .prefetch_related("imagenes")
        .order_by("producto_id")
    )
    return Response(ProductoListSerializer(products, many=True).data)


@api_view(["GET"])
@authentication_classes([CatalogServiceTokenAuthentication])
@permission_classes([IsCatalogService])
def internal_summary(request):
    active_products = Producto.objects.filter(activo=True)
    return Response(
        {
            "productos_activos": active_products.count(),
            "productos_sin_imagen_principal": active_products.exclude(
                imagenes__es_principal=True
            )
            .distinct()
            .count(),
        }
    )
