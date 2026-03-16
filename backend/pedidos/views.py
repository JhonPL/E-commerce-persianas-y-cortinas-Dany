from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Pedido, EstadoPedido, HistorialEstadoPedido, Direccion
from .serializers import (PedidoSerializer, CrearPedidoSerializer,
                           DireccionSerializer)
from usuarios.permissions import EsAdmin


class MisPedidosView(generics.ListAPIView):
    serializer_class   = PedidoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Pedido.objects.filter(
            cliente=self.request.user.cliente
        ).select_related('estado', 'direccion').prefetch_related('detalles')


class CrearPedidoView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CrearPedidoSerializer(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        pedido = serializer.save()
        return Response(PedidoSerializer(pedido).data,
                        status=status.HTTP_201_CREATED)


class DetallePedidoView(generics.RetrieveAPIView):
    serializer_class   = PedidoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Pedido.objects.filter(cliente=self.request.user.cliente)


class CambiarEstadoPedidoView(APIView):
    """Solo admin puede cambiar estado"""
    permission_classes = [EsAdmin]

    def patch(self, request, pk):
        pedido     = generics.get_object_or_404(Pedido, pk=pk)
        estado_id  = request.data.get('estado_id')
        notas      = request.data.get('notas', '')

        try:
            estado = EstadoPedido.objects.get(pk=estado_id)
        except EstadoPedido.DoesNotExist:
            return Response({'error': 'Estado inválido.'}, status=400)

        pedido.estado = estado
        pedido.save()

        HistorialEstadoPedido.objects.create(
            pedido       = pedido,
            estado       = estado,
            cambiado_por = request.user,
            notas_cambio = notas,
        )
        return Response(PedidoSerializer(pedido).data)


class DireccionView(generics.ListCreateAPIView):
    serializer_class   = DireccionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Direccion.objects.filter(
            cliente=self.request.user.cliente
        )

    def perform_create(self, serializer):
        serializer.save(cliente=self.request.user.cliente)