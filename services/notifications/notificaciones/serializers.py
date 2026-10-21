import base64
import binascii
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
    nombre_recibe = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
    )
    direccion = serializers.CharField(max_length=500, required=False, allow_blank=True)
    total = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal("0.00"),
    )
    detalles = PedidoDetalleNotificationSerializer(many=True, allow_empty=False)
    numero_factura = serializers.CharField(max_length=50)
    pdf_base64 = serializers.CharField(max_length=2_000_000, write_only=True)

    def validate_pdf_base64(self, value):
        try:
            pdf = base64.b64decode(value, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise serializers.ValidationError(
                "El adjunto no tiene una codificación válida."
            ) from exc
        if not pdf.startswith(b"%PDF-"):
            raise serializers.ValidationError("El adjunto no es un PDF válido.")
        return value


class PedidoStatusChangedSerializer(serializers.Serializer):
    pedido_id = serializers.IntegerField(min_value=1)
    historial_id = serializers.IntegerField(min_value=1)
    cliente_nombre = serializers.CharField(max_length=150)
    cliente_email = serializers.EmailField(max_length=150)
    estado_anterior = serializers.CharField(max_length=50)
    estado_nuevo = serializers.CharField(max_length=50)
    nombre_recibe = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
    )
    direccion = serializers.CharField(max_length=500, required=False, allow_blank=True)


class ContactMessageSerializer(serializers.Serializer):
    nombre = serializers.CharField(max_length=120)
    email = serializers.EmailField(max_length=150)
    asunto = serializers.CharField(max_length=150, required=False, allow_blank=True)
    mensaje = serializers.CharField(max_length=3000)
