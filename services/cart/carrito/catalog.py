import requests
from django.conf import settings
from rest_framework.exceptions import APIException


class CatalogServiceUnavailable(APIException):
    status_code = 502
    default_detail = "No fue posible consultar el servicio de catálogo."
    default_code = "catalog_service_unavailable"


def get_catalog_products(product_ids, require_all=True):
    normalized_ids = sorted({int(product_id) for product_id in product_ids})
    if not normalized_ids:
        return {}

    if not settings.INTERNAL_SERVICE_TOKEN:
        raise CatalogServiceUnavailable(
            "Falta configurar INTERNAL_SERVICE_TOKEN para consultar el catálogo."
        )

    endpoint = (
        settings.CATALOGO_SERVICE_INTERNAL_URL.rstrip("/") + "/productos/"
    )
    try:
        response = requests.get(
            endpoint,
            params={"ids": ",".join(map(str, normalized_ids))},
            headers={
                "X-Internal-Service-Token": settings.INTERNAL_SERVICE_TOKEN
            },
            timeout=settings.SERVICE_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        products = response.json()
    except requests.RequestException as exc:
        raise CatalogServiceUnavailable() from exc
    except ValueError as exc:
        raise CatalogServiceUnavailable(
            "El servicio de catálogo devolvió una respuesta inválida."
        ) from exc

    if not isinstance(products, list):
        raise CatalogServiceUnavailable(
            "El servicio de catálogo devolvió una respuesta inválida."
        )

    product_map = {}
    try:
        for product in products:
            product_map[int(product["producto_id"])] = product
    except (KeyError, TypeError, ValueError) as exc:
        raise CatalogServiceUnavailable(
            "El servicio de catálogo devolvió productos inválidos."
        ) from exc

    missing_ids = set(normalized_ids) - product_map.keys()
    if require_all and missing_ids:
        raise CatalogServiceUnavailable(
            "El catálogo no contiene todos los productos referenciados."
        )
    return product_map
