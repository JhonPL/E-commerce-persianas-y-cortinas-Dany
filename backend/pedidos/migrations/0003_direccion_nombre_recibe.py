from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("pedidos", "0002_catalog_service_reference"),
    ]

    operations = [
        migrations.AddField(
            model_name="direccion",
            name="nombre_recibe",
            field=models.CharField(blank=True, default="", max_length=100),
        ),
    ]
