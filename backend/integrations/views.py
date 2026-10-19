import hmac

import requests
from django.conf import settings
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.exceptions import APIException
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status



@api_view(["DELETE"])
@authentication_classes([])
@permission_classes([AllowAny])
def prepare_product_deletion(request, product_id):
    expected_token = settings.INTERNAL_SERVICE_TOKEN
    supplied_token = request.headers.get("X-Internal-Service-Token", "")
    if not expected_token or not hmac.compare_digest(
        supplied_token, expected_token
    ):
        return Response(
            {"detail": "No autorizado."},
            status=status.HTTP_403_FORBIDDEN,
        )

    order_endpoint = (
        settings.ORDERS_SERVICE_URL.rstrip("/")
        + f"/api/internal/pedidos/productos/{product_id}/"
    )
    try:
        order_response = requests.get(
            order_endpoint,
            headers={"X-Internal-Service-Token": expected_token},
            timeout=settings.ORDERS_SERVICE_TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        raise ProductReferenceServiceUnavailable(
            "No fue posible comprobar las referencias del producto en pedidos."
        ) from exc

    if order_response.status_code == status.HTTP_409_CONFLICT:
        return Response(
            {"detail": "El producto está asociado a pedidos existentes."},
            status=status.HTTP_409_CONFLICT,
        )
    if order_response.status_code != status.HTTP_200_OK:
        raise ProductReferenceServiceUnavailable(
            "No fue posible comprobar las referencias del producto en pedidos."
        )

    endpoint = (
        settings.CART_SERVICE_INTERNAL_URL.rstrip("/")
        + f"/productos/{product_id}/"
    )
    try:
        response = requests.delete(
            endpoint,
            headers={"X-Internal-Service-Token": expected_token},
            timeout=settings.CART_SERVICE_TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        raise ProductReferenceServiceUnavailable() from exc

    if response.status_code not in (
        status.HTTP_200_OK,
        status.HTTP_204_NO_CONTENT,
    ):
        raise ProductReferenceServiceUnavailable()

    return Response(status=status.HTTP_204_NO_CONTENT)


class ProductReferenceServiceUnavailable(APIException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = "No fue posible validar las referencias del producto en servicios dependientes."
    default_code = "dependent_service_unavailable"
