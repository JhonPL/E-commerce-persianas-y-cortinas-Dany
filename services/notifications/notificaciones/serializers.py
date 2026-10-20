from decimal import Decimal

from rest_framework import serializers


class PedidoDetalleNotificationSerializer(serializers.Serializer):
    producto_id = serializers.IntegerField(min_value=1)
    producto_nombre = serializers.CharField(max_length=150)
    cantidad = serializers.IntegerField(min_value=1)
    ancho_cm = serializers.DecimalField(
        max_digits=8,
        decimal_places=2,
        min_value=Decimal("0.01"),
    )
    alto_cm = serializers.DecimalField(
        max_digits=8,
        decimal_places=2,
        min_value=Decimal("0.01"),
    )
    precio_total = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal("0.00"),
    )


class PedidoApprovedSerializer(serializers.Serializer):
    pedido_id = serializers.IntegerField(min_value=1)
    cliente_nombre = serializers.CharField(max_length=150)
    cliente_email = serializers.EmailField(max_length=150)
    total = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal("0.00"),
    )
    detalles = PedidoDetalleNotificationSerializer(many=True, allow_empty=False)


class PedidoCreatedSerializer(serializers.Serializer):
    pedido_id = serializers.IntegerField(min_value=1)
    cliente_nombre = serializers.CharField(max_length=150)
    cliente_email = serializers.EmailField(max_length=150)
    total = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal("0.00"),
    )
    direccion = serializers.CharField(max_length=500)
    detalles = PedidoDetalleNotificationSerializer(many=True, allow_empty=False)


class PedidoStatusChangedSerializer(serializers.Serializer):
    pedido_id = serializers.IntegerField(min_value=1)
    historial_id = serializers.IntegerField(min_value=1)
    cliente_nombre = serializers.CharField(max_length=150)
    cliente_email = serializers.EmailField(max_length=150)
    estado_anterior = serializers.CharField(max_length=50)
    estado_nuevo = serializers.CharField(max_length=50)


class ContactMessageSerializer(serializers.Serializer):
    nombre = serializers.CharField(max_length=120)
    email = serializers.EmailField(max_length=150)
    asunto = serializers.CharField(max_length=150, required=False, allow_blank=True)
    mensaje = serializers.CharField(max_length=3000)
