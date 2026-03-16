from decimal import Decimal, ROUND_HALF_UP
from rest_framework import serializers
from .models import CarritoItem
from catalogo.serializers import ProductoListSerializer


class CarritoItemSerializer(serializers.ModelSerializer):
    producto_detalle = ProductoListSerializer(source='producto', read_only=True)
    subtotal         = serializers.SerializerMethodField()

    class Meta:
        model  = CarritoItem
        fields = ['item_id', 'producto', 'producto_detalle', 'cantidad',
                  'ancho_cm', 'alto_cm', 'area_m2', 'subtotal', 'fecha_agregado']
        read_only_fields = ['area_m2']

    def get_subtotal(self, obj):
        return float(obj.area_m2 * obj.producto.precio_m2 * obj.cantidad)

    def validate(self, data):
        ancho = data['ancho_cm']
        alto  = data['alto_cm']
        if ancho <= 0 or alto <= 0:
            raise serializers.ValidationError("Las medidas deben ser mayores a 0.")
        # Calcular area automáticamente
        area = (ancho * alto) / Decimal('10000')
        data['area_m2'] = area.quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)
        return data

    def create(self, validated_data):
        usuario = self.context['request'].user
        # Si ya existe el mismo producto con mismas medidas, incrementar cantidad
        item, creado = CarritoItem.objects.get_or_create(
            usuario  = usuario,
            producto = validated_data['producto'],
            ancho_cm = validated_data['ancho_cm'],
            alto_cm  = validated_data['alto_cm'],
            defaults = {'cantidad': validated_data.get('cantidad', 1),
                        'area_m2':  validated_data['area_m2']}
        )
        if not creado:
            item.cantidad += validated_data.get('cantidad', 1)
            item.save()
        return item


class CarritoResumenSerializer(serializers.Serializer):
    items      = CarritoItemSerializer(many=True)
    total_items = serializers.IntegerField()
    total      = serializers.FloatField()