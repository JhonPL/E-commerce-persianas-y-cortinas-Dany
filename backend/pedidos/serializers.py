from rest_framework import serializers
from .models import Pedido, DetallePedido


class DetalleItemSerializer(serializers.ModelSerializer):
    producto_id      = serializers.IntegerField(source='producto', read_only=True)
    nombre           = serializers.SerializerMethodField()
    imagen_principal = serializers.SerializerMethodField()

    class Meta:
        model  = DetallePedido
        fields = [
            'detalle_id', 'producto_id', 'nombre', 'imagen_principal',
            'cantidad', 'ancho_cm', 'alto_cm', 'area_m2',
            'precio_m2', 'precio_total',
        ]

    def get_imagen_principal(self, obj):
        return self._get_product(obj.producto)['imagen_principal']

    def get_nombre(self, obj):
        return self._get_product(obj.producto)['nombre']

    def _get_product(self, product_id):
        products = self.context.get('catalog_products', {})
        product = products.get(product_id)
        if product is None:
            raise serializers.ValidationError(
                f"El producto {product_id} no está disponible en el catálogo."
            )
        return product


class PedidoListSerializer(serializers.ModelSerializer):
    estado_nombre    = serializers.CharField(source='estado.nombre', read_only=True)
    cliente_nombre   = serializers.SerializerMethodField()
    cliente_email    = serializers.SerializerMethodField()
    ciudad           = serializers.CharField(source='direccion.ciudad.nombre', read_only=True)
    num_items        = serializers.SerializerMethodField()

    class Meta:
        model  = Pedido
        fields = [
            'pedido_id', 'fecha_pedido', 'total',
            'estado_id', 'estado_nombre',
            'cliente_nombre', 'cliente_email', 'ciudad',
            'num_items',
        ]

    def get_cliente_nombre(self, obj):
        return obj.cliente.usuario.nombre

    def get_cliente_email(self, obj):
        return obj.cliente.usuario.email

    def get_num_items(self, obj):
        return obj.detalles.count()


class PedidoDetalleSerializer(PedidoListSerializer):
    detalles = DetalleItemSerializer(many=True, read_only=True)
    direccion_completa = serializers.SerializerMethodField()

    class Meta(PedidoListSerializer.Meta):
        fields = PedidoListSerializer.Meta.fields + ['detalles', 'direccion_completa', 'notas']

    def get_direccion_completa(self, obj):
        d = obj.direccion
        return f"{d.calle} #{d.numero}, {d.barrio or ''}, {d.ciudad.nombre}".strip(', ')