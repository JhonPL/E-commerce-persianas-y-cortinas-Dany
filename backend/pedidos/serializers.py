from decimal import Decimal, ROUND_HALF_UP
from rest_framework import serializers
from .models import Pedido, DetallePedido, Direccion, Ciudad, Departamento
from catalogo.models import Producto


class DepartamentoSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Departamento
        fields = ['departamento_id', 'nombre']


class CiudadSerializer(serializers.ModelSerializer):
    departamento = DepartamentoSerializer(read_only=True)

    class Meta:
        model  = Ciudad
        fields = ['ciudad_id', 'nombre', 'departamento']


class DireccionSerializer(serializers.ModelSerializer):
    ciudad_nombre = serializers.CharField(source='ciudad.nombre', read_only=True)

    class Meta:
        model  = Direccion
        fields = ['direccion_id', 'ciudad', 'ciudad_nombre', 'barrio',
                  'calle', 'numero', 'complemento', 'es_principal']


class DetallePedidoSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source='producto.nombre', read_only=True)

    class Meta:
        model  = DetallePedido
        fields = ['detalle_id', 'producto', 'producto_nombre', 'cantidad',
                  'ancho_cm', 'alto_cm', 'area_m2', 'precio_m2', 'precio_total']


class PedidoSerializer(serializers.ModelSerializer):
    detalles      = DetallePedidoSerializer(many=True, read_only=True)
    estado_nombre = serializers.CharField(source='estado.nombre', read_only=True)
    direccion_detalle = DireccionSerializer(source='direccion', read_only=True)

    class Meta:
        model  = Pedido
        fields = ['pedido_id', 'estado', 'estado_nombre', 'fecha_pedido',
                  'total', 'notas', 'direccion', 'direccion_detalle', 'detalles']
        read_only_fields = ['total', 'fecha_pedido']


class CrearPedidoSerializer(serializers.Serializer):
    """Crea un pedido desde el carrito activo"""
    direccion_id = serializers.IntegerField()
    notas        = serializers.CharField(required=False, allow_blank=True)

    def validate_direccion_id(self, value):
        cliente = self.context['request'].user.cliente
        if not Direccion.objects.filter(
                direccion_id=value, cliente=cliente).exists():
            raise serializers.ValidationError("Dirección no válida.")
        return value

    def create(self, validated_data):
        from carrito.models import CarritoItem
        usuario  = self.context['request'].user
        cliente  = usuario.cliente
        carrito  = CarritoItem.objects.filter(usuario=usuario)\
                              .select_related('producto')

        if not carrito.exists():
            raise serializers.ValidationError("El carrito está vacío.")

        total = Decimal('0')
        detalles = []
        for item in carrito:
            precio_total = (item.area_m2 * item.producto.precio_m2 * item.cantidad)\
                           .quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            total += precio_total
            detalles.append({
                'producto':    item.producto,
                'cantidad':    item.cantidad,
                'ancho_cm':    item.ancho_cm,
                'alto_cm':     item.alto_cm,
                'area_m2':     item.area_m2,
                'precio_m2':   item.producto.precio_m2,
                'precio_total': precio_total,
            })

        pedido = Pedido.objects.create(
            cliente    = cliente,
            direccion  = Direccion.objects.get(pk=validated_data['direccion_id']),
            total      = total,
            notas      = validated_data.get('notas', ''),
        )
        for d in detalles:
            DetallePedido.objects.create(pedido=pedido, **d)

        # Vaciar carrito
        carrito.delete()
        return pedido