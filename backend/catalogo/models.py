from django.db import models


class Categoria(models.Model):
    categoria_id = models.AutoField(primary_key=True)
    nombre       = models.CharField(max_length=100)
    descripcion  = models.TextField(null=True, blank=True)
    activo       = models.BooleanField(default=True)

    class Meta:
        db_table = 'categorias'

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    producto_id   = models.AutoField(primary_key=True)
    nombre        = models.CharField(max_length=150)
    descripcion   = models.TextField(null=True, blank=True)
    precio_m2     = models.DecimalField(max_digits=10, decimal_places=2)
    categoria     = models.ForeignKey(Categoria, on_delete=models.PROTECT,
                                      related_name='productos')
    activo        = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'productos'

    def __str__(self):
        return self.nombre


class ImagenProducto(models.Model):
    imagen_id   = models.AutoField(primary_key=True)
    producto    = models.ForeignKey(Producto, on_delete=models.CASCADE,
                                    related_name='imagenes')
    url         = models.URLField(max_length=255)
    es_principal = models.BooleanField(default=False)
    orden       = models.IntegerField(default=0)

    class Meta:
        db_table = 'imagenesproducto'
        ordering = ['orden']