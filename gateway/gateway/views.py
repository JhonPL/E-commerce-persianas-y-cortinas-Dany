import hmac

import requests
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods


def _get_json(url, *, headers=None, timeout=None):
    response = requests.get(
        url,
        headers=headers or {},
        timeout=timeout or settings.SERVICE_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, dict):
        raise ValueError("Se esperaba un objeto JSON.")
    return data


def _service_summary(service, path):
    token = settings.INTERNAL_SERVICE_TOKEN
    if not token:
        raise requests.RequestException("Falta el token interno.")
    return _get_json(
        f"{service.rstrip('/')}/{path.lstrip('/')}",
        headers={"X-Internal-Service-Token": token},
    )


@require_GET
def admin_dashboard(request):
    authorization = request.headers.get("Authorization")
    if not authorization:
        return JsonResponse({"detail": "Se requiere autenticación."}, status=401)
    try:
        identity = _get_json(
            f"{settings.IDENTITY_SERVICE_URL}/api/v1/auth/me/",
            headers={"Authorization": authorization},
        )
    except requests.RequestException:
        return JsonResponse(
            {"detail": "El servicio de identidad no está disponible."},
            status=503,
        )
    except ValueError:
        return JsonResponse(
            {"detail": "El servicio de identidad devolvió una respuesta inválida."},
            status=503,
        )

    if identity.get("rol_nombre") != "admin":
        return JsonResponse({"detail": "No autorizado."}, status=403)

    try:
        orders = _service_summary(
            settings.ORDERS_SERVICE_URL,
            "/api/internal/pedidos/dashboard/",
        )
        customers = _service_summary(
            settings.IDENTITY_SERVICE_URL,
            "/api/internal/identity/resumen/",
        )
        catalog = _service_summary(
            settings.CATALOGO_SERVICE_INTERNAL_URL,
            "/resumen/",
        )
        required = {
            "periodo_label",
            "pedidos_mes_count",
            "pedidos_prev_count",
            "ingresos_mes",
            "pct_pedidos",
            "pct_ingresos",
            "ventas_mes",
            "pedidos_recientes",
            "top_productos",
            "pendientes_48h",
        }
        if (
            not required.issubset(orders)
            or not {"total_clientes", "clientes_mes", "clientes_mes_anterior"}.issubset(customers)
            or not {"productos_activos", "productos_sin_imagen_principal"}.issubset(catalog)
        ):
            raise ValueError("Un servicio devolvió métricas incompletas.")
        metrics = {
            "pedidos_mes": {
                "label": "Pedidos este mes",
                "value": orders["pedidos_mes_count"],
                "delta": orders["pct_pedidos"],
            },
            "ingresos_mes": {
                "label": "Ingresos (COP)",
                "value": orders["ingresos_mes"],
                "delta": orders["pct_ingresos"],
            },
            "productos_activos": {
                "label": "Productos activos",
                "value": catalog["productos_activos"],
                "delta": "0",
            },
            "clientes": {
                "label": "Clientes",
                "value": customers["total_clientes"],
                "delta": _absolute_delta(
                    customers["clientes_mes"],
                    customers["clientes_mes_anterior"],
                ),
            },
        }
    except requests.RequestException:
        return JsonResponse(
            {"detail": "No se pudo consultar un servicio para el dashboard."},
            status=503,
        )
    except (ValueError, TypeError, KeyError):
        return JsonResponse(
            {"detail": "Un servicio devolvió métricas incompletas o inválidas."},
            status=503,
        )

    alerts = []
    if orders["pendientes_48h"]:
        alerts.append(
            {
                "tipo": "warning",
                "msg": (
                    f"{orders['pendientes_48h']} pedidos llevan más de 48h "
                    "en 'Pendiente de preparación'"
                ),
            }
        )
    if catalog["productos_sin_imagen_principal"]:
        alerts.append(
            {
                "tipo": "info",
                "msg": (
                    f"{catalog['productos_sin_imagen_principal']} productos "
                    "activos sin imagen principal"
                ),
            }
        )
    return JsonResponse(
        {
            "periodo_label": orders["periodo_label"],
            "metrics": metrics,
            "ventas_mes": orders["ventas_mes"],
            "pedidos_recientes": orders["pedidos_recientes"],
            "top_productos": orders["top_productos"],
            "alertas": alerts,
        }
    )


def _absolute_delta(actual, previous):
    delta = int(actual) - int(previous)
    return f"+{delta}" if delta > 0 else str(delta)


@csrf_exempt
@require_http_methods(["DELETE"])
def prepare_product_deletion(request, product_id):
    expected = settings.INTERNAL_SERVICE_TOKEN
    supplied = request.headers.get("X-Internal-Service-Token", "")
    if not expected or not hmac.compare_digest(supplied, expected):
        return JsonResponse({"detail": "No autorizado."}, status=403)

    return _prepare_product_deletion(product_id)


def _prepare_product_deletion(product_id):
    expected = settings.INTERNAL_SERVICE_TOKEN
    if not expected:
        return JsonResponse(
            {"detail": "Falta configurar el token interno."},
            status=503,
        )
    headers = {"X-Internal-Service-Token": expected}
    try:
        order_response = requests.get(
            f"{settings.ORDERS_SERVICE_URL}/api/internal/pedidos/productos/{product_id}/",
            headers=headers,
            timeout=settings.SERVICE_TIMEOUT_SECONDS,
        )
    except requests.RequestException:
        return JsonResponse(
            {"detail": "No fue posible consultar las referencias en pedidos."},
            status=503,
        )
    if order_response.status_code == 409:
        return JsonResponse(
            {"detail": "El producto está asociado a pedidos existentes."},
            status=409,
        )
    if order_response.status_code != 200:
        return JsonResponse(
            {"detail": "No fue posible consultar las referencias en pedidos."},
            status=503,
        )

    try:
        cart_response = requests.delete(
            f"{settings.CART_SERVICE_INTERNAL_URL}/productos/{product_id}/",
            headers=headers,
            timeout=settings.SERVICE_TIMEOUT_SECONDS,
        )
    except requests.RequestException:
        return JsonResponse(
            {"detail": "No fue posible limpiar las referencias del carrito."},
            status=503,
        )
    if cart_response.status_code not in (200, 204):
        return JsonResponse(
            {"detail": "No fue posible limpiar las referencias del carrito."},
            status=503,
        )
    return HttpResponse(status=204)


@csrf_exempt
@require_http_methods(["DELETE"])
def delete_catalog_product(request, product_id):
    authorization = request.headers.get("Authorization")
    if not authorization:
        return JsonResponse({"detail": "Se requiere autenticación."}, status=401)

    try:
        identity_response = requests.get(
            f"{settings.IDENTITY_SERVICE_URL}/api/v1/auth/me/",
            headers={"Authorization": authorization},
            timeout=settings.SERVICE_TIMEOUT_SECONDS,
        )
    except requests.RequestException:
        return JsonResponse(
            {"detail": "El servicio de identidad no está disponible."},
            status=503,
        )
    if identity_response.status_code in (401, 403):
        return HttpResponse(
            identity_response.content,
            status=identity_response.status_code,
            content_type=identity_response.headers.get("Content-Type"),
        )
    if identity_response.status_code != 200:
        return JsonResponse(
            {"detail": "El servicio de identidad no está disponible."},
            status=503,
        )
    try:
        identity = identity_response.json()
    except ValueError:
        return JsonResponse(
            {"detail": "El servicio de identidad devolvió una respuesta inválida."},
            status=503,
        )
    if not isinstance(identity, dict):
        return JsonResponse(
            {"detail": "El servicio de identidad devolvió una respuesta inválida."},
            status=503,
        )
    if identity.get("rol_nombre") != "admin":
        return JsonResponse({"detail": "No autorizado."}, status=403)

    preparation = _prepare_product_deletion(product_id)
    if preparation.status_code != 204:
        return preparation

    try:
        catalog_response = requests.delete(
            f"{settings.CATALOGO_SERVICE_URL}/productos/{product_id}/",
            headers={"Authorization": authorization},
            timeout=settings.SERVICE_TIMEOUT_SECONDS,
            allow_redirects=False,
        )
    except requests.RequestException:
        return JsonResponse(
            {"detail": "El servicio de catálogo no está disponible."},
            status=503,
        )

    response = HttpResponse(
        catalog_response.content,
        status=catalog_response.status_code,
        content_type=catalog_response.headers.get("Content-Type"),
    )
    for header in ("Allow", "Location"):
        if value := catalog_response.headers.get(header):
            response[header] = value
    return response
