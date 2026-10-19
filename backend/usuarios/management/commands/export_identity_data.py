import json
import os
from pathlib import Path

from django.core.management import BaseCommand, CommandError
from usuarios.models import Cliente, Rol, Usuario


class Command(BaseCommand):
    help = (
        "Exporta roles, usuarios y perfiles a un archivo local sensible "
        "para transferirlos al servicio de identidad."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            required=True,
            type=Path,
            help="Ruta del archivo JSON de transferencia fuera del repositorio.",
        )

    def handle(self, *args, **options):
        destination = options["file"].expanduser().resolve()
        project_root = Path(__file__).resolve().parents[4]
        if destination.is_relative_to(project_root):
            raise CommandError(
                "El archivo de transferencia debe guardarse fuera del proyecto."
            )
        destination.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "roles": list(
                Rol.objects.order_by("rol_id").values("rol_id", "nombre")
            ),
            "usuarios": [],
            "clientes": list(
                Cliente.objects.order_by("cliente_id").values(
                    "cliente_id",
                    "usuario_id",
                    "telefono",
                    "documento_tipo",
                    "documento_numero",
                )
            ),
        }
        for user in Usuario.objects.order_by("usuario_id").iterator():
            registered = user.fecha_registro
            last_login = user.last_login
            payload["usuarios"].append(
                {
                    "usuario_id": user.usuario_id,
                    "nombre": user.nombre,
                    "email": user.email,
                    "password": user.password,
                    "proveedor_auth": user.proveedor_auth,
                    "proveedor_id": user.proveedor_id,
                    "rol_id": user.rol_id,
                    "activo": user.activo,
                    "fecha_registro": registered.isoformat(),
                    "last_login": last_login.isoformat() if last_login else None,
                    "is_staff": user.is_staff,
                    "is_superuser": user.is_superuser,
                }
            )

        try:
            descriptor = os.open(
                destination,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                0o600,
            )
            with os.fdopen(descriptor, "w", encoding="utf-8") as output:
                json.dump(payload, output, ensure_ascii=False)
                output.write("\n")
        except OSError as exc:
            raise CommandError("No se pudo guardar el archivo de transferencia.") from exc

        self.stdout.write(
            self.style.SUCCESS(
                f"Transferencia creada con {len(payload['usuarios'])} usuarios y "
                f"{len(payload['clientes'])} perfiles. Proteja y elimine el archivo "
                "después de verificar la importación."
            )
        )
