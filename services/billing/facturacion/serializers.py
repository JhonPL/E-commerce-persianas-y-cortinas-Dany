from rest_framework import serializers
from decimal import Decimal

from .models import Factura


class DemoInvoiceDetailSerializer(serializers.Serializer):
    producto_id = serializers.IntegerField(min_value=1)
    producto_nombre = serializers.CharField(max_length=150)
    categoria_nombre = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
    )
    descripcion = serializers.CharField(
        required=False,
        allow_blank=True,
    )
    cantidad = serializers.IntegerField(min_value=1)
    ancho_cm = serializers.DecimalField(max_digits=8, decimal_places=2, min_value=Decimal("0.01"))
    alto_cm = serializers.DecimalField(max_digits=8, decimal_places=2, min_value=Decimal("0.01"))
    precio_total = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal("0.00"))


class DemoInvoiceSerializer(serializers.Serializer):
    pedido_id = serializers.IntegerField(min_value=1)
    cliente_nombre = serializers.CharField(max_length=150)
    cliente_email = serializers.EmailField(max_length=150)
    nombre_recibe = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
    )
    direccion = serializers.CharField(max_length=500, allow_blank=True)
    identificacion = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
    )
    telefono = serializers.CharField(
        max_length=50,
        required=False,
        allow_blank=True,
    )
    estado_pedido = serializers.CharField(max_length=50, required=False)
    estado_pago = serializers.CharField(max_length=100, required=False)
    metodo_pago = serializers.CharField(max_length=100, required=False)
    observaciones = serializers.CharField(required=False, allow_blank=True)
    importe_pagado = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal("0.00"),
        required=False,
    )
    saldo_pendiente = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal("0.00"),
        required=False,
    )
    total = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal("0.00"))
    detalles = DemoInvoiceDetailSerializer(many=True, allow_empty=False)

    def validate(self, data):
        details_total = sum(
            (item["precio_total"] for item in data["detalles"]),
            Decimal("0.00"),
        )
        if details_total != data["total"]:
            raise serializers.ValidationError(
                {"total": "El total no coincide con el detalle del pedido."}
            )
        return data


class FacturaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Factura
        fields = [
            "factura_id",
            "pedido_id",
            "numero_factura",
            "cufe",
            "xml_path",
            "pdf_path",
            "enviada_dian",
            "estado",
            "fecha_emision",
            "fecha_vencimiento",
        ]
        read_only_fields = ["factura_id", "fecha_emision"]
