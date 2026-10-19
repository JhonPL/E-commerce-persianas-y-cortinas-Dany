from django.db import migrations


def seed_checkout_states(apps, schema_editor):
    state_model = apps.get_model("pedidos", "EstadoPedido")
    for name in (
        "Pendiente de preparación",
        "Pendiente de pago",
        "Pago rechazado",
        "Preparado",
        "Enviado",
    ):
        state_model.objects.get_or_create(nombre=name)


class Migration(migrations.Migration):
    dependencies = [
        ("pedidos", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_checkout_states, migrations.RunPython.noop),
    ]