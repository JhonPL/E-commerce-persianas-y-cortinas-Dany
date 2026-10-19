import uuid

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="PaymentAttempt",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                (
                    "payment_reference",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        unique=True,
                    ),
                ),
                ("request_id", models.UUIDField()),
                ("pedido_id", models.PositiveIntegerField()),
                ("usuario_id", models.PositiveIntegerField()),
                ("amount", models.DecimalField(decimal_places=2, max_digits=10)),
                (
                    "outcome",
                    models.CharField(
                        choices=[
                            ("approved", "Aprobado (simulado)"),
                            ("declined", "Rechazado (simulado)"),
                        ],
                        max_length=12,
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
            ],
            options={
                "db_table": "payment_simulation_attempts",
                "ordering": ["created_at", "id"],
            },
        ),
        migrations.AddConstraint(
            model_name="paymentattempt",
            constraint=models.UniqueConstraint(
                fields=("pedido_id", "request_id"),
                name="unique_payment_request_per_order",
            ),
        ),
    ]