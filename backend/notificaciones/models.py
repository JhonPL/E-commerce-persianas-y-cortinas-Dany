from django.db import models
from pedidos.models import Pedido


class NotificacionAdmin(models.Model):
    ENVIADO      = 'enviado'
    FALLIDO      = 'fallido'
    REINTENTANDO = 'reintentando'
    PENDIENTE    = 'pendiente'

    notif_id     = models.AutoField(primary_key=True)
    pedido       = models.ForeignKey(Pedido, on_delete=models.CASCADE,
                                     related_name='notificaciones')
    destinatario = models.EmailField(max_length=150)
    estado       = models.CharField(max_length=50, default=PENDIENTE)
    fecha_envio  = models.DateTimeField(auto_now_add=True)
    intentos     = models.IntegerField(default=1)
    error_detalle = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'notificacionesadmin'