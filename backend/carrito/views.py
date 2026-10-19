from decimal import Decimal, InvalidOperation

from django.db import transaction
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from .models import CarritoItem
from .serializers import CarritoItemSerializer
from integrations.catalogo import get_catalog_products


def _carrito_response(usuario):
    """Helper: devuelve el carrito completo del usuario."""
    items = list(
        CarritoItem.objects
        .filter(usuario=usuario)
    )
    catalog_products = get_catalog_products(item.producto for item in items)
    serializer = CarritoItemSerializer(
        items,
        many=True,
        context={'catalog_products': catalog_products},
    )
    serialized_items = serializer.data
    total = sum(item['subtotal'] for item in serialized_items)
    return {
        'items':       serialized_items,
        'total_items': len(items),
        'total':       round(total, 2),
    }


class CarritoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(_carrito_response(request.user))

    def post(self, request):
        serializer = CarritoItemSerializer(
            data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            serializer.save()
            response_data = _carrito_response(request.user)
        return Response(response_data, status=status.HTTP_201_CREATED)


class CarritoItemView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class   = CarritoItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return CarritoItem.objects.filter(usuario=self.request.user)

    def get_object(self):
        return generics.get_object_or_404(
            self.get_queryset(), pk=self.kwargs['pk']
        )

    def update(self, request, *args, **kwargs):
        with transaction.atomic():
            item = self.get_object()
            cantidad = request.data.get('cantidad')
            if cantidad is not None:
                cantidad = int(cantidad)
                if cantidad <= 0:
                    item.delete()
                else:
                    item.cantidad = cantidad
                    item.save()
            response_data = _carrito_response(request.user)
        return Response(response_data)

    def destroy(self, request, *args, **kwargs):
        with transaction.atomic():
            self.get_object().delete()
            response_data = _carrito_response(request.user)
        return Response(response_data)


class LimpiarCarritoView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        CarritoItem.objects.filter(usuario=request.user).delete()
        return Response({'items': [], 'total_items': 0, 'total': 0.0})


class SincronizarCarritoView(APIView):
    """
    POST /api/v1/carrito/sincronizar/
    Fusiona el carrito local (navegador) con el carrito en BD al hacer login.
    Body: { "items": [{ "producto": <id>, "ancho_cm": x, "alto_cm": y, "cantidad": n }] }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        items_locales = request.data.get('items', [])
        if not isinstance(items_locales, list):
            return Response(
                {'detail': 'items debe ser una lista.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        normalized_items = []
        errores_items = []
        for index, item_data in enumerate(items_locales):
            try:
                if not isinstance(item_data, dict):
                    raise ValueError
                product_id = int(
                    item_data.get('producto') or item_data.get('producto_id')
                )
                width = Decimal(str(item_data['ancho_cm']))
                height = Decimal(str(item_data['alto_cm']))
                quantity = int(item_data.get('cantidad', 1))
                if product_id <= 0 or width <= 0 or height <= 0 or quantity <= 0:
                    raise ValueError
                normalized_items.append(
                    (index, product_id, width, height, quantity)
                )
            except (KeyError, TypeError, ValueError, InvalidOperation):
                errores_items.append(
                    {'indice': index, 'detail': 'El ítem del carrito no es válido.'}
                )

        products = get_catalog_products(
            (product_id for _, product_id, *_ in normalized_items),
            require_all=False,
        )
        with transaction.atomic():
            for index, product_id, width, height, quantity in normalized_items:
                product = products.get(product_id)
                if product is None or not product['activo']:
                    errores_items.append(
                        {
                            'indice': index,
                            'detail': 'El producto no existe o está inactivo.',
                        }
                    )
                    continue

                item, created = CarritoItem.objects.get_or_create(
                    usuario=request.user,
                    producto=product_id,
                    ancho_cm=width,
                    alto_cm=height,
                    defaults={'cantidad': quantity},
                )
                if not created:
                    item.cantidad += quantity
                    item.save()

            response_data = _carrito_response(request.user)
        if errores_items:
            response_data['errores_items'] = errores_items
        return Response(response_data)