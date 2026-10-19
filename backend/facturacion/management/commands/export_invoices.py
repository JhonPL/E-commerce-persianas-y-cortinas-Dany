import json
import os
from pathlib import Path

from django.core.management import BaseCommand, CommandError

from facturacion.models import Factura


class Command(BaseCommand):
    help = "Exporta facturas legacy a un archivo JSON fuera del repositorio."

    def add_arguments(self, parser):
        parser.add_argument("--file", required=True, type=Path)

    def handle(self, *args, **options):
        destination = options["file"].expanduser().resolve()
        project_root = Path(__file__).resolve().parents[4]
        if destination.is_relative_to(project_root):
            raise CommandError(
                "El archivo de transferencia debe guardarse fuera del proyecto."
            )
        payload = {
            "facturas": list(
                Factura.objects.order_by("factura_id").values(
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
                )
            )
        }
        destination.parent.mkdir(parents=True, exist_ok=True)
        try:
            descriptor = os.open(
                destination,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                0o600,
            )
            with os.fdopen(descriptor, "w", encoding="utf-8") as output:
                json.dump(payload, output, ensure_ascii=False, default=str)
                output.write("\n")
        except OSError as exc:
            raise CommandError(
                "No se pudo guardar el archivo de transferencia."
            ) from exc
        self.stdout.write(
            self.style.SUCCESS(
                f"Exportación completa: {len(payload['facturas'])} facturas."
            )
        )
