import requests
from django.conf import settings
from rest_framework.exceptions import APIException


class OrdersServiceUnavailable(APIException):
    status_code = 502
    default_detail = "No fue posible consultar el servicio de pedidos."
    default_code = "orders_service_unavailable"


def get_orders_dashboard():
    if not settings.INTERNAL_SERVICE_TOKEN:
        raise OrdersServiceUnavailable(
            "Falta configurar INTERNAL_SERVICE_TOKEN para consultar pedidos."
        )

    endpoint = (
        settings.ORDERS_SERVICE_URL.rstrip("/")
        + "/api/internal/pedidos/dashboard/"
    )
    try:
        response = requests.get(
            endpoint,
            headers={
                "X-Internal-Service-Token": settings.INTERNAL_SERVICE_TOKEN
            },
            timeout=settings.ORDERS_SERVICE_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as exc:
        raise OrdersServiceUnavailable() from exc
    except ValueError as exc:
        raise OrdersServiceUnavailable(
            "El servicio de pedidos devolvió una respuesta inválida."
        ) from exc

    required_keys = {
        "periodo_label",
        "pedidos_mes_count",
        "pedidos_prev_count",
        "ingresos_mes",
        "ingresos_prev",
        "ventas_mes",
        "pedidos_recientes",
        "top_productos",
        "pendientes_48h",
        "pct_pedidos",
        "pct_ingresos",
    }
    if not isinstance(data, dict) or not required_keys.issubset(data):
        raise OrdersServiceUnavailable(
            "El servicio de pedidos devolvió una respuesta inválida."
        )
    return data
