from django.db import models
from usuarios.models import Usuario
from catalogo.models import Producto


class CarritoItem(models.Model):
    item_id        = models.AutoField(primary_key=True)
    usuario        = models.ForeignKey(Usuario, on_delete=models.CASCADE,
                                       related_name='carrito')
    producto       = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad       = models.IntegerField(default=1)
    ancho_cm       = models.DecimalField(max_digits=8, decimal_places=2)
    alto_cm        = models.DecimalField(max_digits=8, decimal_places=2)
    area_m2        = models.DecimalField(max_digits=10, decimal_places=4)
    fecha_agregado = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'carritoitems'
        unique_together = [['usuario', 'producto', 'ancho_cm', 'alto_cm']]