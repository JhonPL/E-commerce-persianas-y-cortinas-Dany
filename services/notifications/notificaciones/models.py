from django.db import models
from django.utils import timezone


class NotificacionAdmin(models.Model):
    ENVIADO = "enviado"
    FALLIDO = "fallido"
    REINTENTANDO = "reintentando"
    PENDIENTE = "pendiente"
    ESTADOS = [
        (ENVIADO, "Enviado"),
        (FALLIDO, "Fallido"),
        (REINTENTANDO, "Reintentando"),
        (PENDIENTE, "Pendiente"),
    ]

    notif_id = models.AutoField(primary_key=True)
    pedido_id = models.PositiveIntegerField(db_index=True)
    evento_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    destinatario = models.EmailField(max_length=150)
    estado = models.CharField(max_length=50, choices=ESTADOS, default=PENDIENTE)
    fecha_envio = models.DateTimeField(default=timezone.now)
    actualizado_en = models.DateTimeField(auto_now=True)
    intentos = models.IntegerField(default=1)
    error_detalle = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "notificacionesadmin"
        ordering = ["-fecha_envio"]
