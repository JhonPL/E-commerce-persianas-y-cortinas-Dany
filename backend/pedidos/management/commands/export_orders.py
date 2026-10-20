import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

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
    help = "Export order data and customer snapshots without identity credentials."

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            required=True,
            help="Destination JSON path for the order-service import.",
        )

    def handle(self, *args, **options):
        output = Path(options["output"])
        orders = list(
            Pedido.objects.select_related(
                "cliente__usuario",
                "direccion__ciudad__departamento",
                "estado",
            ).order_by("pedido_id")
        )
        order_ids = [order.pedido_id for order in orders]
        address_ids = {order.direccion_id for order in orders}
        addresses = list(
            Direccion.objects.filter(direccion_id__in=address_ids)
            .select_related("cliente__usuario", "ciudad__departamento")
            .order_by("direccion_id")
        )
        city_ids = {address.ciudad_id for address in addresses}
        cities = list(
            Ciudad.objects.filter(ciudad_id__in=city_ids)
            .select_related("departamento")
            .order_by("ciudad_id")
        )
        department_ids = {city.departamento_id for city in cities}
        departments = list(
            Departamento.objects.filter(
                departamento_id__in=department_ids
            ).order_by("departamento_id")
        )
        details = list(
            DetallePedido.objects.filter(pedido_id__in=order_ids).order_by(
                "detalle_id"
            )
        )
        histories = list(
            HistorialEstadoPedido.objects.filter(
                pedido_id__in=order_ids
            ).order_by("historial_id")
        )

        payload = {
            "schema_version": 1,
            "departamentos": [
                {
                    "departamento_id": item.departamento_id,
                    "nombre": item.nombre,
                }
                for item in departments
            ],
            "ciudades": [
                {
                    "ciudad_id": item.ciudad_id,
                    "nombre": item.nombre,
                    "departamento_id": item.departamento_id,
                }
                for item in cities
            ],
            "direcciones": [
                {
                    "direccion_id": item.direccion_id,
                    "usuario_id": item.cliente.usuario_id,
                    "ciudad_id": item.ciudad_id,
                    "nombre_recibe": item.nombre_recibe,
                    "barrio": item.barrio,
                    "calle": item.calle,
                    "numero": item.numero,
                    "complemento": item.complemento,
                    "es_principal": item.es_principal,
                }
                for item in addresses
            ],
            "estados": [
                {"estado_id": item.estado_id, "nombre": item.nombre}
                for item in EstadoPedido.objects.order_by("estado_id")
            ],
            "pedidos": [
                {
                    "pedido_id": item.pedido_id,
                    "usuario_id": item.cliente.usuario_id,
                    "cliente_nombre": item.cliente.usuario.nombre,
                    "cliente_email": item.cliente.usuario.email,
                    "direccion_id": item.direccion_id,
                    "estado_id": item.estado_id,
                    "fecha_pedido": item.fecha_pedido.isoformat(),
                    "total": str(item.total),
                    "referencia_pago": item.referencia_pago,
                    "notas": item.notas,
                }
                for item in orders
            ],
            "detalles": [
                {
                    "detalle_id": item.detalle_id,
                    "pedido_id": item.pedido_id,
                    "producto_id": item.producto,
                    "cantidad": item.cantidad,
                    "ancho_cm": str(item.ancho_cm),
                    "alto_cm": str(item.alto_cm),
                    "area_m2": str(item.area_m2),
                    "precio_m2": str(item.precio_m2),
                    "precio_total": str(item.precio_total),
                }
                for item in details
            ],
            "historial": [
                {
                    "historial_id": item.historial_id,
                    "pedido_id": item.pedido_id,
                    "estado_id": item.estado_id,
                    "cambiado_en": item.cambiado_en.isoformat(),
                    "cambiado_por_id": item.cambiado_por_id,
                    "notas_cambio": item.notas_cambio,
                }
                for item in histories
            ],
        }
        try:
            output.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError as exc:
            raise CommandError(f"No se pudo escribir el archivo {output}.") from exc

        self.stdout.write(
            self.style.SUCCESS(
                f"Exported {len(orders)} orders and {len(details)} details to {output}."
            )
        )
