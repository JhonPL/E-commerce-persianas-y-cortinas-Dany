from django.db import models
from django.utils import timezone


class Factura(models.Model):
    GENERADA = "generada"
    TRANSMITIDA = "transmitida"
    ACEPTADA = "aceptada"
    RECHAZADA = "rechazada"
    ESTADOS = [
        (GENERADA, "Generada"),
        (TRANSMITIDA, "Transmitida"),
        (ACEPTADA, "Aceptada"),
        (RECHAZADA, "Rechazada"),
    ]

    factura_id = models.AutoField(primary_key=True)
    pedido_id = models.PositiveIntegerField(unique=True)
    numero_factura = models.CharField(max_length=50, unique=True)
    cufe = models.CharField(max_length=255, unique=True)
    xml_path = models.URLField(max_length=255, null=True, blank=True)
    pdf_path = models.URLField(max_length=255, null=True, blank=True)
    enviada_dian = models.BooleanField(default=False)
    estado = models.CharField(max_length=50, choices=ESTADOS, default=GENERADA)
    fecha_emision = models.DateTimeField(default=timezone.now)
    fecha_vencimiento = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "facturas"
        ordering = ["-fecha_emision"]

    def __str__(self):
        return f"Factura {self.numero_factura} — Pedido {self.pedido_id}"
