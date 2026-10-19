from rest_framework import serializers

from .models import Factura


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
