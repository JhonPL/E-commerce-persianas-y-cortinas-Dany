from decimal import Decimal

from rest_framework import serializers


class PedidoApprovedSerializer(serializers.Serializer):
    pedido_id = serializers.IntegerField(min_value=1)
    cliente_email = serializers.EmailField(max_length=150)
    total = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal("0.00"),
    )
