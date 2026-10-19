from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("catalogo", "0001_initial"),
        ("pedidos", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="detallepedido",
            name="producto",
            field=models.PositiveIntegerField(db_column="producto_id"),
        ),
    ]
