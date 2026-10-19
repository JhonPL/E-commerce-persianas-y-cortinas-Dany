import json
import os
from pathlib import Path

from django.core.management import BaseCommand, CommandError

from notificaciones.models import NotificacionAdmin


class Command(BaseCommand):
    help = "Exporta el historial de notificaciones a un archivo local protegido."

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
            "notificaciones": list(
                NotificacionAdmin.objects.order_by("notif_id").values(
                    "notif_id",
                    "pedido_id",
                    "destinatario",
                    "estado",
                    "fecha_envio",
                    "intentos",
                    "error_detalle",
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
                f"Transferencia creada con {len(payload['notificaciones'])} "
                "registros. Proteja y elimine el archivo después de verificar "
                "la importación."
            )
        )
