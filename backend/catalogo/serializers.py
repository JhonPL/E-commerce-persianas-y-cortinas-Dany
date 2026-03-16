from rest_framework import serializers
from .models import Categoria, Producto, ImagenProducto


class ImagenProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model  = ImagenProducto
        fields = ['imagen_id', 'url', 'es_principal', 'orden']


class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Categoria
        fields = ['categoria_id', 'nombre', 'descripcion', 'activo']


class ProductoListSerializer(serializers.ModelSerializer):
    """Para listado del catálogo — ligero"""
    imagen_principal = serializers.SerializerMethodField()
    categoria_nombre = serializers.CharField(source='categoria.nombre', read_only=True)

    class Meta:
        model  = Producto
        fields = ['producto_id', 'nombre', 'precio_m2',
                  'categoria_nombre', 'imagen_principal']

    def get_imagen_principal(self, obj):
        img = obj.imagenes.filter(es_principal=True).first()
        return img.url if img else None


class ProductoDetalleSerializer(serializers.ModelSerializer):
    """Para vista de detalle — completo"""
    imagenes         = ImagenProductoSerializer(many=True, read_only=True)
    categoria_nombre = serializers.CharField(source='categoria.nombre', read_only=True)

    class Meta:
        model  = Producto
        fields = ['producto_id', 'nombre', 'descripcion', 'precio_m2',
                  'categoria', 'categoria_nombre', 'activo',
                  'fecha_creacion', 'imagenes']


class ProductoAdminSerializer(serializers.ModelSerializer):
    """Para crear/editar productos — solo admin"""
    class Meta:
        model  = Producto
        fields = ['nombre', 'descripcion', 'precio_m2', 'categoria', 'activo']