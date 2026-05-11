# facturacion/models.py
from django.db import models
from pedidos.models import Pedido


class Factura(models.Model):
    ESTADOS = [
        ('generada',    'Generada'),
        ('transmitida', 'Transmitida'),
        ('aceptada',    'Aceptada'),
        ('rechazada',   'Rechazada'),
    ]

    factura_id        = models.AutoField(primary_key=True)
    pedido            = models.OneToOneField(Pedido, on_delete=models.CASCADE,
                                             related_name='factura')
    numero_factura    = models.CharField(max_length=50, unique=True)
    cufe              = models.CharField(max_length=255, unique=True)
    xml_path          = models.URLField(max_length=255, null=True, blank=True)
    pdf_path          = models.URLField(max_length=255, null=True, blank=True)
    enviada_dian      = models.BooleanField(default=False)
    estado            = models.CharField(max_length=50, choices=ESTADOS,
                                         default='generada')
    fecha_emision     = models.DateTimeField(auto_now_add=True)
    fecha_vencimiento = models.DateField(null=True, blank=True)

    class Meta:
        db_table = 'facturas'

    def __str__(self):
        return f"Factura {self.numero_factura} — Pedido {self.pedido_id}"