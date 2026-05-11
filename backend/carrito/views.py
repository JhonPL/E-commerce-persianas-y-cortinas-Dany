# backend/carrito/views.py
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .models import CarritoItem
from .serializers import CarritoItemSerializer


def _carrito_response(usuario):
    """Helper: devuelve el carrito completo del usuario."""
    items = (
        CarritoItem.objects
        .filter(usuario=usuario)
        .select_related('producto')
        .prefetch_related('producto__imagenes')
    )
    serializer = CarritoItemSerializer(items, many=True)
    total = sum(i.get_subtotal() for i in items)
    return {
        'items':       serializer.data,
        'total_items': items.count(),
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
        serializer.save()
        # Devolver el carrito completo para que el frontend sincronice
        return Response(_carrito_response(request.user), status=status.HTTP_201_CREATED)


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
        item = self.get_object()
        cantidad = request.data.get('cantidad')
        if cantidad is not None:
            cantidad = int(cantidad)
            if cantidad <= 0:
                item.delete()
                return Response(_carrito_response(request.user))
            item.cantidad = cantidad
            item.save()
        return Response(_carrito_response(request.user))

    def destroy(self, request, *args, **kwargs):
        self.get_object().delete()
        return Response(_carrito_response(request.user))


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
        for item_data in items_locales:
            try:
                from catalogo.models import Producto
                from decimal import Decimal
                producto = Producto.objects.get(
                    producto_id=item_data.get('producto') or item_data.get('producto_id'),
                    activo=True
                )
                ancho_cm = Decimal(str(item_data['ancho_cm']))
                alto_cm  = Decimal(str(item_data['alto_cm']))
                cantidad = int(item_data.get('cantidad', 1))

                item, created = CarritoItem.objects.get_or_create(
                    usuario    = request.user,
                    producto   = producto,
                    ancho_cm   = ancho_cm,
                    alto_cm    = alto_cm,
                    defaults   = {'cantidad': cantidad},
                )
                if not created:
                    item.cantidad += cantidad
                    item.save()
            except Exception:
                continue  # Ítem inválido — ignorar sin abortar

        return Response(_carrito_response(request.user))