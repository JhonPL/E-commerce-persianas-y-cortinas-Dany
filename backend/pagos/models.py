from django.db import models
from pedidos.models import Pedido


class MetodoPago(models.Model):
    metodo_id = models.AutoField(primary_key=True)
    nombre    = models.CharField(max_length=50)

    class Meta:
        db_table = 'metodospago'


class Pago(models.Model):
    APROBADO  = 'aprobado'
    RECHAZADO = 'rechazado'
    PENDIENTE = 'pendiente'
    ESTADO_CHOICES = [
        (APROBADO,  'Aprobado'),
        (RECHAZADO, 'Rechazado'),
        (PENDIENTE, 'Pendiente'),
    ]

    pago_id             = models.AutoField(primary_key=True)
    pedido              = models.OneToOneField(Pedido, on_delete=models.CASCADE,
                                               related_name='pago')
    metodo              = models.ForeignKey(MetodoPago, on_delete=models.PROTECT)
    monto               = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_pago          = models.DateTimeField(auto_now_add=True)
    estado_pago         = models.CharField(max_length=50, choices=ESTADO_CHOICES,
                                           default=PENDIENTE)
    referencia_pasarela = models.CharField(max_length=100, unique=True)

    class Meta:
        db_table = 'pagos'