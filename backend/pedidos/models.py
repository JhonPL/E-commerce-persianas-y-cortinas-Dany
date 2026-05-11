from django.db import models
from usuarios.models import Usuario, Cliente
from catalogo.models import Producto


class Departamento(models.Model):
    departamento_id = models.AutoField(primary_key=True)
    nombre          = models.CharField(max_length=100)

    class Meta:
        db_table = 'departamentos'


class Ciudad(models.Model):
    ciudad_id      = models.AutoField(primary_key=True)
    nombre         = models.CharField(max_length=100)
    departamento   = models.ForeignKey(Departamento, on_delete=models.CASCADE,
                                       related_name='ciudades')

    class Meta:
        db_table = 'ciudades'


class Direccion(models.Model):
    direccion_id = models.AutoField(primary_key=True)
    cliente      = models.ForeignKey(Cliente, on_delete=models.CASCADE,
                                     related_name='direcciones')
    ciudad       = models.ForeignKey(Ciudad, on_delete=models.PROTECT)
    barrio       = models.CharField(max_length=100, null=True, blank=True)
    calle        = models.CharField(max_length=150)
    numero       = models.CharField(max_length=50)
    complemento  = models.CharField(max_length=150, null=True, blank=True)
    es_principal = models.BooleanField(default=False)

    class Meta:
        db_table = 'direcciones'


class EstadoPedido(models.Model):
    PENDIENTE  = 'Pendiente de preparación'
    PREPARADO  = 'Preparado'
    ENVIADO    = 'Enviado'

    estado_id = models.AutoField(primary_key=True)
    nombre    = models.CharField(max_length=50)

    class Meta:
        db_table = 'estadospedido'


class Pedido(models.Model):
    pedido_id       = models.AutoField(primary_key=True)
    cliente         = models.ForeignKey(Cliente, on_delete=models.PROTECT,
                                        related_name='pedidos')
    direccion       = models.ForeignKey(Direccion, on_delete=models.PROTECT)
    estado          = models.ForeignKey(EstadoPedido, on_delete=models.PROTECT,
                                        default=1)
    fecha_pedido    = models.DateTimeField(auto_now_add=True)
    total           = models.DecimalField(max_digits=10, decimal_places=2)
    referencia_pago = models.CharField(max_length=100, null=True, blank=True)
    notas           = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'pedidos'


class DetallePedido(models.Model):
    detalle_id   = models.AutoField(primary_key=True)
    pedido       = models.ForeignKey(Pedido, on_delete=models.CASCADE,
                                     related_name='detalles')
    producto     = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad     = models.IntegerField(default=1)
    ancho_cm     = models.DecimalField(max_digits=8,  decimal_places=2)
    alto_cm      = models.DecimalField(max_digits=8,  decimal_places=2)
    area_m2      = models.DecimalField(max_digits=10, decimal_places=4)
    precio_m2    = models.DecimalField(max_digits=10, decimal_places=2)
    precio_total = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'detallepedido'


class HistorialEstadoPedido(models.Model):
    historial_id = models.AutoField(primary_key=True)
    pedido       = models.ForeignKey(Pedido, on_delete=models.CASCADE,
                                     related_name='historial')
    estado       = models.ForeignKey(EstadoPedido, on_delete=models.PROTECT)
    cambiado_en  = models.DateTimeField(auto_now_add=True)
    cambiado_por = models.ForeignKey(Usuario, on_delete=models.PROTECT)
    notas_cambio = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'historialestadospedido'
        ordering = ['-cambiado_en']