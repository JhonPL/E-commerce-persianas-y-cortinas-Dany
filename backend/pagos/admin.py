from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Pago, MetodoPago

admin.site.register(Pago)
admin.site.register(MetodoPago)