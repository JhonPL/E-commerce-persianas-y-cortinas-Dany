# backend/carrito/serializers.py
from decimal import Decimal
from rest_framework import serializers
from .models import CarritoItem
from integrations.catalogo import get_catalog_products


class CarritoItemSerializer(serializers.ModelSerializer):
    producto = serializers.IntegerField(min_value=1)
    producto_detalle = serializers.SerializerMethodField()
    subtotal         = serializers.SerializerMethodField()
    # Exponer también campos sueltos que usa el frontend
    producto_id      = serializers.IntegerField(source='producto', read_only=True)
    nombre           = serializers.SerializerMethodField()
    precio_m2        = serializers.SerializerMethodField()
    imagen_principal = serializers.SerializerMethodField()

    class Meta:
        model  = CarritoItem
        fields = [
            'item_id', 'producto', 'producto_id', 'nombre',
            'imagen_principal', 'precio_m2',
            'producto_detalle', 'cantidad',
            'ancho_cm', 'alto_cm', 'area_m2', 'subtotal', 'fecha_agregado',
        ]
        read_only_fields = ['area_m2', 'item_id']

    def get_subtotal(self, obj):
        product = self._get_product(obj.producto)
        return obj.get_subtotal(product['precio_m2'])

    def get_producto_detalle(self, obj):
        return self._get_product(obj.producto)

    def get_nombre(self, obj):
        return self._get_product(obj.producto)['nombre']

    def get_precio_m2(self, obj):
        return self._get_product(obj.producto)['precio_m2']

    def get_imagen_principal(self, obj):
        return self._get_product(obj.producto)['imagen_principal']

    def _get_product(self, product_id):
        products = self.context.get('catalog_products')
        if products is None:
            products = get_catalog_products([product_id])
        product = products.get(product_id)
        if product is None:
            raise serializers.ValidationError(
                f"El producto {product_id} ya no está disponible en el catálogo."
            )
        return product

    def validate(self, data):
        ancho = Decimal(str(data.get('ancho_cm', 0)))
        alto  = Decimal(str(data.get('alto_cm', 0)))
        if ancho <= 0 or alto <= 0:
            raise serializers.ValidationError("Las medidas deben ser mayores a 0.")
        return data

    def validate_producto(self, value):
        products = get_catalog_products([value], require_all=False)
        if value not in products:
            raise serializers.ValidationError(
                "El producto seleccionado no existe en el catálogo."
            )
        return value

    def create(self, validated_data):
        usuario = self.context['request'].user
        item, creado = CarritoItem.objects.get_or_create(
            usuario  = usuario,
            producto = validated_data['producto'],
            ancho_cm = validated_data['ancho_cm'],
            alto_cm  = validated_data['alto_cm'],
            defaults = {'cantidad': validated_data.get('cantidad', 1)},
        )
        if not creado:
            item.cantidad += validated_data.get('cantidad', 1)
            item.save()
        return item


class CarritoResumenSerializer(serializers.Serializer):
    items       = CarritoItemSerializer(many=True)
    total_items = serializers.IntegerField()
    total       = serializers.FloatField()