import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.core.management.color import no_style
from django.db import connection, transaction
from django.utils.dateparse import parse_datetime

from pedidos.models import (
    Ciudad,
    Departamento,
    DetallePedido,
    Direccion,
    EstadoPedido,
    HistorialEstadoPedido,
    Pedido,
)


class Command(BaseCommand):
    help = "Import order data exported by the monolith's export_orders command."

    def add_arguments(self, parser):
        parser.add_argument(
            "--input",
            required=True,
            help="Path to the JSON produced by export_orders.",
        )

    def handle(self, *args, **options):
        source = Path(options["input"])
        try:
            payload = json.loads(source.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise CommandError(f"No se pudo leer el archivo {source}.") from exc
        if not isinstance(payload, dict) or payload.get("schema_version") != 1:
            raise CommandError("El archivo no usa el formato de exportación v1.")

        expected = (
            "departamentos",
            "ciudades",
            "direcciones",
            "estados",
            "pedidos",
            "detalles",
            "historial",
        )
        for key in expected:
            if not isinstance(payload.get(key), list):
                raise CommandError(f"El campo {key} debe ser una lista.")

        models = (
            Departamento,
            Ciudad,
            Direccion,
            EstadoPedido,
            Pedido,
            DetallePedido,
            HistorialEstadoPedido,
        )
        non_state_models = tuple(model for model in models if model is not EstadoPedido)
        seeded_state_names = {
            "Pendiente de preparación",
            "Pendiente de pago",
            "Pago rechazado",
            "Preparado",
            "Enviado",
        }
        existing_state_names = set(
            EstadoPedido.objects.values_list("nombre", flat=True)
        )
        if (
            any(model.objects.exists() for model in non_state_models)
            or not existing_state_names.issubset(seeded_state_names)
        ):
            raise CommandError(
                "La base de pedidos no está vacía; no se importaron datos."
            )

        try:
            with transaction.atomic():
                EstadoPedido.objects.all().delete()
                Departamento.objects.bulk_create(
                    [
                        Departamento(
                            departamento_id=item["departamento_id"],
                            nombre=item["nombre"],
                        )
                        for item in payload["departamentos"]
                    ]
                )
                Ciudad.objects.bulk_create(
                    [
                        Ciudad(
                            ciudad_id=item["ciudad_id"],
                            nombre=item["nombre"],
                            departamento_id=item["departamento_id"],
                        )
                        for item in payload["ciudades"]
                    ]
                )
                EstadoPedido.objects.bulk_create(
                    [
                        EstadoPedido(
                            estado_id=item["estado_id"],
                            nombre=item["nombre"],
                        )
                        for item in payload["estados"]
                    ]
                )
                Direccion.objects.bulk_create(
                    [
                        Direccion(
                            direccion_id=item["direccion_id"],
                            usuario=item["usuario_id"],
                            ciudad_id=item["ciudad_id"],
                            nombre_recibe=item.get("nombre_recibe", ""),
                            barrio=item["barrio"],
                            calle=item["calle"],
                            numero=item["numero"],
                            complemento=item["complemento"],
                            es_principal=item["es_principal"],
                        )
                        for item in payload["direcciones"]
                    ]
                )
                Pedido.objects.bulk_create(
                    [
                        Pedido(
                            pedido_id=item["pedido_id"],
                            usuario=item["usuario_id"],
                            cliente_nombre=item["cliente_nombre"],
                            cliente_email=item["cliente_email"],
                            direccion_id=item["direccion_id"],
                            estado_id=item["estado_id"],
                            fecha_pedido=self._parse_datetime(
                                item["fecha_pedido"]
                            ),
                            total=item["total"],
                            referencia_pago=item["referencia_pago"],
                            notas=item["notas"],
                        )
                        for item in payload["pedidos"]
                    ]
                )
                DetallePedido.objects.bulk_create(
                    [
                        DetallePedido(
                            detalle_id=item["detalle_id"],
                            pedido_id=item["pedido_id"],
                            producto=item["producto_id"],
                            producto_nombre=item.get("producto_nombre", ""),
                            cantidad=item["cantidad"],
                            ancho_cm=item["ancho_cm"],
                            alto_cm=item["alto_cm"],
                            area_m2=item["area_m2"],
                            precio_m2=item["precio_m2"],
                            precio_total=item["precio_total"],
                        )
                        for item in payload["detalles"]
                    ]
                )
                HistorialEstadoPedido.objects.bulk_create(
                    [
                        HistorialEstadoPedido(
                            historial_id=item["historial_id"],
                            pedido_id=item["pedido_id"],
                            estado_id=item["estado_id"],
                            cambiado_en=self._parse_datetime(
                                item["cambiado_en"]
                            ),
                            cambiado_por=item["cambiado_por_id"],
                            notas_cambio=item["notas_cambio"],
                        )
                        for item in payload["historial"]
                    ]
                )
                self._reset_sequences(models)
        except (KeyError, TypeError, ValueError) as exc:
            raise CommandError("El archivo contiene registros inválidos.") from exc

        self.stdout.write(
            self.style.SUCCESS(
                f"Imported {len(payload['pedidos'])} orders and "
                f"{len(payload['detalles'])} details."
            )
        )

    @staticmethod
    def _parse_datetime(value):
        parsed = parse_datetime(value)
        if parsed is None:
            raise ValueError("Invalid datetime.")
        return parsed

    @staticmethod
    def _reset_sequences(models):
        sql_statements = connection.ops.sequence_reset_sql(no_style(), models)
        with connection.cursor() as cursor:
            for statement in sql_statements:
                cursor.execute(statement)
