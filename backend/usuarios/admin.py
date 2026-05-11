from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Usuario, Cliente, Rol

admin.site.register(Rol)
admin.site.register(Usuario)
admin.site.register(Cliente)