from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="CarritoItem",
            fields=[
                (
                    "item_id",
                    models.AutoField(primary_key=True, serialize=False),
                ),
                (
                    "usuario",
                    models.PositiveIntegerField(db_column="usuario_id"),
                ),
                (
                    "producto",
                    models.PositiveIntegerField(db_column="producto_id"),
                ),
                ("cantidad", models.IntegerField(default=1)),
                ("ancho_cm", models.DecimalField(decimal_places=2, max_digits=8)),
                ("alto_cm", models.DecimalField(decimal_places=2, max_digits=8)),
                (
                    "area_m2",
                    models.DecimalField(decimal_places=4, max_digits=10),
                ),
                ("fecha_agregado", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "db_table": "carritoitems",
                "unique_together": {("usuario", "producto", "ancho_cm", "alto_cm")},
            },
        ),
    ]
