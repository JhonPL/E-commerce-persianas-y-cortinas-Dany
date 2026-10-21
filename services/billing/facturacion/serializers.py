from rest_framework import serializers
from decimal import Decimal

from .models import Factura


class DemoInvoiceDetailSerializer(serializers.Serializer):
    producto_id = serializers.IntegerField(min_value=1)
    producto_nombre = serializers.CharField(max_length=150)
    cantidad = serializers.IntegerField(min_value=1)
    ancho_cm = serializers.DecimalField(max_digits=8, decimal_places=2, min_value=Decimal("0.01"))
    alto_cm = serializers.DecimalField(max_digits=8, decimal_places=2, min_value=Decimal("0.01"))
    precio_total = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal("0.00"))


class DemoInvoiceSerializer(serializers.Serializer):
    pedido_id = serializers.IntegerField(min_value=1)
    cliente_nombre = serializers.CharField(max_length=150)
    cliente_email = serializers.EmailField(max_length=150)
    direccion = serializers.CharField(max_length=500, allow_blank=True)
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
