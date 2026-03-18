from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Pedido, DetallePedido, EstadoPedido, Direccion, Ciudad, Departamento, HistorialEstadoPedido

admin.site.register(Pedido)
admin.site.register(DetallePedido)
admin.site.register(EstadoPedido)
admin.site.register(Direccion)
admin.site.register(Ciudad)
admin.site.register(Departamento)
admin.site.register(HistorialEstadoPedido)