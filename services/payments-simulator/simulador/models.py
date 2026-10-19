import uuid

from django.db import models
from django.utils import timezone


class PaymentAttempt(models.Model):
    class Outcome(models.TextChoices):
        APPROVED = "approved", "Aprobado (simulado)"
        DECLINED = "declined", "Rechazado (simulado)"

    id = models.BigAutoField(primary_key=True)
    payment_reference = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    request_id = models.UUIDField()
    pedido_id = models.PositiveIntegerField()
    usuario_id = models.PositiveIntegerField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    outcome = models.CharField(max_length=12, choices=Outcome.choices)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "payment_simulation_attempts"
        constraints = [
            models.UniqueConstraint(
                fields=["pedido_id", "request_id"],
                name="unique_payment_request_per_order",
            )
        ]
        ordering = ["created_at", "id"]