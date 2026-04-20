# backend/carrito/serializers.py
from decimal import Decimal, ROUND_HALF_UP
from rest_framework import serializers
from .models import CarritoItem
from catalogo.serializers import ProductoListSerializer


class CarritoItemSerializer(serializers.ModelSerializer):
    producto_detalle = ProductoListSerializer(source='producto', read_only=True)
    subtotal         = serializers.SerializerMethodField()
    # Exponer también campos sueltos que usa el frontend
    producto_id      = serializers.IntegerField(source='producto.producto_id', read_only=True)
    nombre           = serializers.CharField(source='producto.nombre', read_only=True)
    precio_m2        = serializers.DecimalField(
        source='producto.precio_m2', max_digits=10, decimal_places=2, read_only=True
    )
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
        return obj.get_subtotal()

    def get_imagen_principal(self, obj):
        img = obj.producto.imagenes.filter(es_principal=True).first() \
           or obj.producto.imagenes.first()
        return img.url if img else None

    def validate(self, data):
        ancho = Decimal(str(data.get('ancho_cm', 0)))
        alto  = Decimal(str(data.get('alto_cm', 0)))
        if ancho <= 0 or alto <= 0:
            raise serializers.ValidationError("Las medidas deben ser mayores a 0.")
        return data

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