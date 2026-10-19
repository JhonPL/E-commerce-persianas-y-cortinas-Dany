import json
from pathlib import Path

from django.core.management import BaseCommand, CommandError
from django.core.management.color import no_style
from django.db import connection, transaction
from django.utils.dateparse import parse_datetime

from usuarios.models import Cliente, Rol, Usuario


class Command(BaseCommand):
    help = "Importa usuarios, roles y perfiles desde un archivo de transferencia protegido."

    def add_arguments(self, parser):
        parser.add_argument("file", type=Path)

    def handle(self, *args, **options):
        transfer_file = options["file"]
        try:
            payload = json.loads(transfer_file.read_text(encoding="utf-8"))
            roles = payload["roles"]
            users = payload["usuarios"]
            clients = payload["clientes"]
        except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
            raise CommandError("El archivo de transferencia no tiene el formato esperado.") from exc

        if not all(isinstance(rows, list) for rows in (roles, users, clients)):
            raise CommandError("El archivo de transferencia no tiene el formato esperado.")
        if any(
            not parse_datetime(row.get("fecha_registro", ""))
            for row in users
            if isinstance(row, dict)
        ) or any(not isinstance(row, dict) for row in users):
            raise CommandError("El archivo contiene una fecha de registro inválida.")

        if Rol.objects.exists() or Usuario.objects.exists() or Cliente.objects.exists():
            raise CommandError(
                "La base de identidad no está vacía; se canceló la importación."
            )
        try:
            with transaction.atomic():
                Rol.objects.bulk_create(
                    [
                        Rol(rol_id=row["rol_id"], nombre=row["nombre"])
                        for row in roles
                    ]
                )
                Usuario.objects.bulk_create(
                    [
                        Usuario(
                            usuario_id=row["usuario_id"],
                            nombre=row["nombre"],
                            email=row["email"],
                            password=row["password"],
                            proveedor_auth=row["proveedor_auth"],
                            proveedor_id=row.get("proveedor_id"),
                            rol_id=row["rol_id"],
                            activo=row["activo"],
                            fecha_registro=parse_datetime(row["fecha_registro"]),
                            last_login=parse_datetime(row["last_login"])
                            if row.get("last_login")
                            else None,
                            is_staff=row["is_staff"],
                            is_superuser=row["is_superuser"],
                        )
                        for row in users
                    ]
                )
                Cliente.objects.bulk_create(
                    [
                        Cliente(
                            cliente_id=row["cliente_id"],
                            usuario_id=row["usuario_id"],
                            telefono=row.get("telefono"),
                            documento_tipo=row.get("documento_tipo"),
                            documento_numero=row.get("documento_numero"),
                        )
                        for row in clients
                    ]
                )
                models = [Rol, Usuario, Cliente]
                statements = connection.ops.sequence_reset_sql(no_style(), models)
                with connection.cursor() as cursor:
                    for statement in statements:
                        cursor.execute(statement)
        except (KeyError, TypeError, ValueError) as exc:
            raise CommandError(
                "El archivo de transferencia contiene datos inválidos; no se importó."
            ) from exc

        self.stdout.write(
            self.style.SUCCESS(
                f"Importación completa: {len(roles)} roles, {len(users)} usuarios, "
                f"{len(clients)} perfiles."
            )
        )
