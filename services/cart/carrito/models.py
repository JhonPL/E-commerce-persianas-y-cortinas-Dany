from decimal import Decimal, ROUND_HALF_UP

from django.db import models


class CarritoItem(models.Model):
    item_id = models.AutoField(primary_key=True)
    usuario = models.PositiveIntegerField(db_column="usuario_id")
    producto = models.PositiveIntegerField(db_column="producto_id")
    cantidad = models.IntegerField(default=1)
    ancho_cm = models.DecimalField(max_digits=8, decimal_places=2)
    alto_cm = models.DecimalField(max_digits=8, decimal_places=2)
    area_m2 = models.DecimalField(max_digits=10, decimal_places=4)
    fecha_agregado = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "carritoitems"
        unique_together = [["usuario", "producto", "ancho_cm", "alto_cm"]]

    def save(self, *args, **kwargs):
        area = (Decimal(str(self.ancho_cm)) * Decimal(str(self.alto_cm))) / Decimal(
            "10000"
        )
        self.area_m2 = area.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
        super().save(*args, **kwargs)

    def get_subtotal(self, precio_m2):
        return round(float(self.area_m2) * float(precio_m2) * self.cantidad, 2)

    def __str__(self):
        return (
            f"Usuario {self.usuario} | Producto {self.producto} | "
            f"{self.ancho_cm}x{self.alto_cm}cm"
        )
