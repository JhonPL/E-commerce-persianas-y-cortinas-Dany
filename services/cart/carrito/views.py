from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.db import transaction
from rest_framework import generics, status
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .authentication import InternalServiceTokenAuthentication
from .catalog import get_catalog_products
from .models import CarritoItem
from .serializers import CarritoItemSerializer


def _carrito_response(user_id):
    items = list(CarritoItem.objects.filter(usuario=user_id))
    catalog_products = get_catalog_products(item.producto for item in items)
    serializer = CarritoItemSerializer(
        items,
        many=True,
        context={"catalog_products": catalog_products},
    )
    serialized_items = serializer.data
    total = sum(item["subtotal"] for item in serialized_items)
    return {
        "items": serialized_items,
        "total_items": len(items),
        "total": round(total, 2),
    }


class CarritoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(_carrito_response(request.user.usuario_id))

    def post(self, request):
        serializer = CarritoItemSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            serializer.save()
            response_data = _carrito_response(request.user.usuario_id)
        return Response(response_data, status=status.HTTP_201_CREATED)


class CarritoItemView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CarritoItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return CarritoItem.objects.filter(usuario=self.request.user.usuario_id)

    def update(self, request, *args, **kwargs):
        with transaction.atomic():
            item = self.get_object()
            cantidad = request.data.get("cantidad")
            if cantidad is not None:
                try:
                    cantidad = int(cantidad)
                except (TypeError, ValueError) as exc:
                    raise ValidationError(
                        "La cantidad debe ser un número entero."
                    ) from exc
                if cantidad <= 0:
                    item.delete()
                else:
                    item.cantidad = cantidad
                    item.save()
            response_data = _carrito_response(request.user.usuario_id)
        return Response(response_data)

    def destroy(self, request, *args, **kwargs):
        with transaction.atomic():
            self.get_object().delete()
            response_data = _carrito_response(request.user.usuario_id)
        return Response(response_data)


class LimpiarCarritoView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        CarritoItem.objects.filter(usuario=request.user.usuario_id).delete()
        return Response({"items": [], "total_items": 0, "total": 0.0})


class SincronizarCarritoView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        local_items = request.data.get("items", [])
        if not isinstance(local_items, list):
            return Response(
                {"detail": "items debe ser una lista."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        normalized_items = []
        item_errors = []
        for index, item_data in enumerate(local_items):
            try:
                if not isinstance(item_data, dict):
                    raise ValueError
                product_id = int(
                    item_data.get("producto") or item_data.get("producto_id")
                )
                width = Decimal(str(item_data["ancho_cm"]))
                height = Decimal(str(item_data["alto_cm"]))
                quantity = int(item_data.get("cantidad", 1))
                if product_id <= 0 or width <= 0 or height <= 0 or quantity <= 0:
                    raise ValueError
                normalized_items.append(
                    (index, product_id, width, height, quantity)
                )
            except (KeyError, TypeError, ValueError, InvalidOperation):
                item_errors.append(
                    {
                        "indice": index,
                        "detail": "El ítem del carrito no es válido.",
                    }
                )

        products = get_catalog_products(
            (product_id for _, product_id, *_ in normalized_items),
            require_all=False,
        )
        with transaction.atomic():
            for index, product_id, width, height, quantity in normalized_items:
                product = products.get(product_id)
                if product is None or not product["activo"]:
                    item_errors.append(
                        {
                            "indice": index,
                            "detail": "El producto no existe o está inactivo.",
                        }
                    )
                    continue

                item, created = CarritoItem.objects.get_or_create(
                    usuario=request.user.usuario_id,
                    producto=product_id,
                    ancho_cm=width,
                    alto_cm=height,
                    defaults={"cantidad": quantity},
                )
                if not created:
                    item.cantidad += quantity
                    item.save()

            response_data = _carrito_response(request.user.usuario_id)
        if item_errors:
            response_data["errores_items"] = item_errors
        return Response(response_data)


@api_view(["DELETE"])
@authentication_classes([InternalServiceTokenAuthentication])
@permission_classes([IsAuthenticated])
def delete_product_references(request, product_id):
    if not getattr(request.user, "is_internal_service", False):
        raise AuthenticationFailed("Se requiere autenticación de servicio.")
    CarritoItem.objects.filter(producto=product_id).delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
