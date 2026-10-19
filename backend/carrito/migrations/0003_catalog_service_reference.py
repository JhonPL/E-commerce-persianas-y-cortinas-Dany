from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("carrito", "0002_alter_carritoitem_usuario"),
        ("catalogo", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="carritoitem",
            name="producto",
            field=models.PositiveIntegerField(db_column="producto_id"),
        ),
    ]
