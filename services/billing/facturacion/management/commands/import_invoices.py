import json
from pathlib import Path

from django.core.management import BaseCommand, CommandError
from django.core.management.color import no_style
from django.db import connection, transaction
from django.utils.dateparse import parse_date, parse_datetime

from facturacion.models import Factura


class Command(BaseCommand):
    help = "Importa facturas en una base vacía."

    def add_arguments(self, parser):
        parser.add_argument("file", type=Path)

    def handle(self, *args, **options):
        try:
            payload = json.loads(options["file"].read_text(encoding="utf-8"))
            rows = payload["facturas"]
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
            "factura_id",
            "pedido_id",
            "numero_factura",
            "cufe",
            "xml_path",
            "pdf_path",
            "enviada_dian",
            "estado",
            "fecha_emision",
            "fecha_vencimiento",
        }
        invoices = []
        for row in rows:
            if not required_fields.issubset(row):
                raise CommandError("El archivo contiene facturas incompletas.")
            issued_at = parse_datetime(row["fecha_emision"])
            due_date = (
                parse_date(row["fecha_vencimiento"])
                if row["fecha_vencimiento"]
                else None
            )
            if issued_at is None or (row["fecha_vencimiento"] and due_date is None):
                raise CommandError(
                    "El archivo contiene una fecha de factura inválida."
                )
            invoices.append(
                Factura(
                    factura_id=row["factura_id"],
                    pedido_id=row["pedido_id"],
                    numero_factura=row["numero_factura"],
                    cufe=row["cufe"],
                    xml_path=row["xml_path"],
                    pdf_path=row["pdf_path"],
                    enviada_dian=row["enviada_dian"],
                    estado=row["estado"],
                    fecha_emision=issued_at,
                    fecha_vencimiento=due_date,
                )
            )

        if Factura.objects.exists():
            raise CommandError(
                "La base de facturación no está vacía; se canceló la importación."
            )
        try:
            with transaction.atomic():
                Factura.objects.bulk_create(invoices)
                statements = connection.ops.sequence_reset_sql(
                    no_style(),
                    [Factura],
                )
                with connection.cursor() as cursor:
                    for statement in statements:
                        cursor.execute(statement)
        except (TypeError, ValueError) as exc:
            raise CommandError(
                "Los datos de transferencia contienen valores inválidos."
            ) from exc

        self.stdout.write(
            self.style.SUCCESS(f"Importación completa: {len(invoices)} facturas.")
        )
