from decimal import Decimal, InvalidOperation
import uuid

import requests
from django.conf import settings
from django.db import IntegrityError, transaction
from rest_framework import serializers, status
from rest_framework.exceptions import APIException
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import PaymentAttempt


class OrdersServiceUnavailable(APIException):
    status_code = 503
    default_detail = "El servicio de pedidos no está disponible."
    default_code = "orders_service_unavailable"


class PaymentSimulationSerializer(serializers.Serializer):
    pedido_id = serializers.IntegerField(min_value=1)
    outcome = serializers.ChoiceField(
        choices=PaymentAttempt.Outcome.choices,
    )
    request_id = serializers.UUIDField()


def _orders_url(pedido_id, suffix):
    return (
        settings.ORDERS_SERVICE_URL.rstrip("/")
        + f"/api/internal/pedidos/{pedido_id}/{suffix}/"
    )


def _orders_request(method, url, **kwargs):
    headers = {
        "X-Internal-Service-Token": settings.INTERNAL_SERVICE_TOKEN,
        **kwargs.pop("headers", {}),
    }
    try:
        response = requests.request(
            method,
            url,
            headers=headers,
            timeout=settings.SERVICE_TIMEOUT_SECONDS,
            **kwargs,
        )
    except requests.RequestException as exc:
        raise OrdersServiceUnavailable() from exc
    if response.status_code == 404:
        return response
    if response.status_code >= 500:
        raise OrdersServiceUnavailable()
    return response


class SimulatePaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not settings.PAYMENT_SIMULATOR_ENABLED:
            return Response(
                {"detail": "El simulador de pagos está deshabilitado."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        if not settings.INTERNAL_SERVICE_TOKEN:
            raise OrdersServiceUnavailable(
                "Falta configurar la autenticación interna entre servicios."
            )

        serializer = PaymentSimulationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        order_id = data["pedido_id"]
        outcome = data["outcome"]
        request_id = data["request_id"]

        attempt = PaymentAttempt.objects.filter(
            pedido_id=order_id,
            request_id=request_id,
        ).first()
        created = False
        if attempt:
            if (
                attempt.usuario_id != request.user.usuario_id
                or attempt.outcome != outcome
            ):
                return Response(
                    {"detail": "La clave de idempotencia ya se usó con otros datos."},
                    status=status.HTTP_409_CONFLICT,
                )
        else:
            context_response = _orders_request(
                "GET",
                _orders_url(order_id, "payment-context"),
            )
            if context_response.status_code == 404:
                return Response(
                    {"detail": "No se encontró el pedido."},
                    status=status.HTTP_404_NOT_FOUND,
                )
            if context_response.status_code == 409:
                return Response(
                    context_response.json(),
                    status=status.HTTP_409_CONFLICT,
                )
            if context_response.status_code != 200:
                raise OrdersServiceUnavailable()

            try:
                order = context_response.json()
                owner_id = int(order["usuario_id"])
                amount = Decimal(str(order["total"])).quantize(Decimal("0.01"))
            except (KeyError, TypeError, ValueError, InvalidOperation) as exc:
                raise OrdersServiceUnavailable(
                    "El servicio de pedidos devolvió datos inválidos."
                ) from exc
            if owner_id != request.user.usuario_id:
                return Response(
                    {"detail": "No se encontró el pedido."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            try:
                with transaction.atomic():
                    attempt, created = PaymentAttempt.objects.get_or_create(
                        pedido_id=order_id,
                        request_id=request_id,
                        defaults={
                            "usuario_id": request.user.usuario_id,
                            "amount": amount,
                            "outcome": outcome,
                        },
                    )
            except IntegrityError:
                attempt = PaymentAttempt.objects.get(
                    pedido_id=order_id,
                    request_id=request_id,
                )
                created = False

            if (
                attempt.usuario_id != request.user.usuario_id
                or attempt.amount != amount
                or attempt.outcome != outcome
            ):
                return Response(
                    {"detail": "La clave de idempotencia ya se usó con otros datos."},
                    status=status.HTTP_409_CONFLICT,
                )

        result_response = _orders_request(
            "POST",
            _orders_url(order_id, "payment-result"),
            json={
                "outcome": attempt.outcome,
                "payment_reference": str(attempt.payment_reference),
                "amount": str(attempt.amount),
            },
        )
        if result_response.status_code == 409:
            return Response(result_response.json(), status=status.HTTP_409_CONFLICT)
        if result_response.status_code != 200:
            raise OrdersServiceUnavailable()

        return Response(
            {
                "pedido_id": order_id,
                "payment_reference": str(attempt.payment_reference),
                "outcome": attempt.outcome,
                "amount": str(attempt.amount),
                "simulated": True,
                "duplicate": not created,
            },
            status=status.HTTP_200_OK,
        )