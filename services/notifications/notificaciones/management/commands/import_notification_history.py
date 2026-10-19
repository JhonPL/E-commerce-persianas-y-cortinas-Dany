import json
from pathlib import Path

from django.core.management import BaseCommand, CommandError
from django.core.management.color import no_style
from django.db import connection, transaction
from django.utils.dateparse import parse_datetime

from notificaciones.models import NotificacionAdmin


class Command(BaseCommand):
    help = "Importa historial desde un archivo de transferencia en una base vacía."

    def add_arguments(self, parser):
        parser.add_argument("file", type=Path)

    def handle(self, *args, **options):
        try:
            payload = json.loads(options["file"].read_text(encoding="utf-8"))
            rows = payload["notificaciones"]
        except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
            raise CommandError(
                "El archivo de transferencia no tiene el formato esperado."
            ) from exc
        if not isinstance(rows, list) or any(
            not isinstance(row, dict) for row in rows
        ):
            raise CommandError(
                "El archivo de transferencia no tiene el formato esperado."
            )

        required_fields = {
            "notif_id",
            "pedido_id",
            "destinatario",
            "estado",
            "fecha_envio",
            "intentos",
            "error_detalle",
        }
        records = []
        for row in rows:
            if not required_fields.issubset(row):
                raise CommandError(
                    "El archivo contiene registros incompletos."
                )
            timestamp = parse_datetime(row["fecha_envio"])
            if timestamp is None:
                raise CommandError(
                    "El archivo contiene una fecha de envío inválida."
                )
            records.append(
                NotificacionAdmin(
                    notif_id=row["notif_id"],
                    pedido_id=row["pedido_id"],
                    destinatario=row["destinatario"],
                    estado=row["estado"],
                    fecha_envio=timestamp,
                    intentos=row["intentos"],
                    error_detalle=row["error_detalle"],
                )
            )

        if NotificacionAdmin.objects.exists():
            raise CommandError(
                "La base de notificaciones no está vacía; se canceló la importación."
            )
        try:
            with transaction.atomic():
                NotificacionAdmin.objects.bulk_create(records)
                statements = connection.ops.sequence_reset_sql(
                    no_style(),
                    [NotificacionAdmin],
                )
                with connection.cursor() as cursor:
                    for statement in statements:
                        cursor.execute(statement)
        except (TypeError, ValueError) as exc:
            raise CommandError(
                "Los registros de transferencia contienen datos inválidos."
            ) from exc

        self.stdout.write(
            self.style.SUCCESS(
                f"Importación completa: {len(records)} notificaciones."
            )
        )
