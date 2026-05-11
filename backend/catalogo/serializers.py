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
                  'categoria', 'categoria_nombre', 'imagen_principal', 'activo']
 
    def get_imagen_principal(self, obj):
        # Primero busca la marcada como principal
        img = obj.imagenes.filter(es_principal=True).first()
        # Si no hay ninguna marcada, toma la primera disponible
        if not img:
            img = obj.imagenes.order_by('orden').first()
        return img.url if img else None
 
 
class ProductoDetalleSerializer(serializers.ModelSerializer):
    """Para vista de detalle — completo con todas las imágenes"""
    imagenes         = ImagenProductoSerializer(many=True, read_only=True)
    categoria_nombre = serializers.CharField(source='categoria.nombre', read_only=True)
 
    class Meta:
        model  = Producto
        fields = ['producto_id', 'nombre', 'descripcion', 'precio_m2',
                  'categoria', 'categoria_nombre', 'activo',
                  'fecha_creacion', 'imagenes']
 
 
class ProductoAdminSerializer(serializers.ModelSerializer):
    """Para crear/editar productos desde el panel admin"""
    class Meta:
        model  = Producto
        fields = ['producto_id', 'nombre', 'descripcion',
                  'precio_m2', 'categoria', 'activo']
        read_only_fields = ['producto_id']