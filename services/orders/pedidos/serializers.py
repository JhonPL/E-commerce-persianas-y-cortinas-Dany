from rest_framework import serializers

from .catalog import get_catalog_products
from .models import DetallePedido, Pedido


class DetalleItemSerializer(serializers.ModelSerializer):
    producto_id = serializers.IntegerField(source="producto", read_only=True)
    nombre = serializers.SerializerMethodField()
    imagen_principal = serializers.SerializerMethodField()

    class Meta:
        model = DetallePedido
        fields = [
            "detalle_id",
            "producto_id",
            "nombre",
            "imagen_principal",
            "cantidad",
            "ancho_cm",
            "alto_cm",
            "area_m2",
            "precio_m2",
            "precio_total",
        ]

    def get_imagen_principal(self, obj):
        return self._get_product(obj.producto)["imagen_principal"]

    def get_nombre(self, obj):
        if obj.producto_nombre:
            return obj.producto_nombre
        return self._get_product(obj.producto)["nombre"]

    def _get_product(self, product_id):
        products = self.context.get("catalog_products", {})
        product = products.get(product_id)
        if product is None:
            raise serializers.ValidationError(
                f"El producto {product_id} no está disponible en el catálogo."
            )
        return product


class PedidoListSerializer(serializers.ModelSerializer):
    estado_nombre = serializers.CharField(source="estado.nombre", read_only=True)
    cliente_nombre = serializers.CharField(read_only=True)
    cliente_email = serializers.CharField(read_only=True)
    ciudad = serializers.CharField(
        source="direccion.ciudad.nombre",
        read_only=True,
    )
    num_items = serializers.SerializerMethodField()

    class Meta:
        model = Pedido
        fields = [
            "pedido_id",
            "fecha_pedido",
            "total",
            "estado_id",
            "estado_nombre",
            "cliente_nombre",
            "cliente_email",
            "ciudad",
            "num_items",
        ]

    def get_num_items(self, obj):
        return obj.detalles.count()


class PedidoDetalleSerializer(PedidoListSerializer):
    detalles = DetalleItemSerializer(many=True, read_only=True)
    direccion_completa = serializers.SerializerMethodField()

    class Meta(PedidoListSerializer.Meta):
        fields = PedidoListSerializer.Meta.fields + [
            "detalles",
            "direccion_completa",
            "notas",
        ]

    def get_direccion_completa(self, obj):
        address = obj.direccion
        return (
            f"{address.calle} #{address.numero}, "
            f"{address.barrio or ''}, {address.ciudad.nombre}"
        ).strip(", ")
