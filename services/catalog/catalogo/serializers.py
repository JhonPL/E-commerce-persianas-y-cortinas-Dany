from rest_framework import serializers

from .models import Categoria, ImagenProducto, Producto


class ImagenProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImagenProducto
        fields = ["imagen_id", "url", "es_principal", "orden"]


class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = ["categoria_id", "nombre", "descripcion", "activo"]


class ProductoListSerializer(serializers.ModelSerializer):
    imagen_principal = serializers.SerializerMethodField()
    categoria_nombre = serializers.CharField(source="categoria.nombre", read_only=True)

    class Meta:
        model = Producto
        fields = [
            "producto_id",
            "nombre",
            "precio_m2",
            "categoria",
            "categoria_nombre",
            "imagen_principal",
            "activo",
        ]

    def get_imagen_principal(self, obj):
        imagen = obj.imagenes.filter(es_principal=True).first()
        if imagen is None:
            imagen = obj.imagenes.order_by("orden").first()
        return imagen.url if imagen else None


class ProductoDetalleSerializer(serializers.ModelSerializer):
    imagenes = ImagenProductoSerializer(many=True, read_only=True)
    categoria_nombre = serializers.CharField(source="categoria.nombre", read_only=True)

    class Meta:
        model = Producto
        fields = [
            "producto_id",
            "nombre",
            "descripcion",
            "precio_m2",
            "categoria",
            "categoria_nombre",
            "activo",
            "fecha_creacion",
            "imagenes",
        ]


class ProductoAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Producto
        fields = [
            "producto_id",
            "nombre",
            "descripcion",
            "precio_m2",
            "categoria",
            "activo",
        ]
        read_only_fields = ["producto_id"]
