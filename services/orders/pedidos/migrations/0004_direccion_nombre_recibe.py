from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("pedidos", "0003_detallepedido_producto_nombre"),
    ]

    operations = [
        migrations.AddField(
            model_name="direccion",
            name="nombre_recibe",
            field=models.CharField(blank=True, default="", max_length=100),
        ),
    ]
