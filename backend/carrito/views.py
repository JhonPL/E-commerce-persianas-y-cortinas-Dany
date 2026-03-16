from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .models import CarritoItem
from .serializers import CarritoItemSerializer


class CarritoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        items = CarritoItem.objects.filter(usuario=request.user)\
                           .select_related('producto')
        serializer = CarritoItemSerializer(items, many=True)
        total = sum(i['subtotal'] for i in serializer.data)
        return Response({
            'items':       serializer.data,
            'total_items': items.count(),
            'total':       round(total, 2),
        })

    def post(self, request):
        serializer = CarritoItemSerializer(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CarritoItemView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class   = CarritoItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return CarritoItem.objects.filter(usuario=self.request.user)

    def get_object(self):
        return generics.get_object_or_404(
            self.get_queryset(), pk=self.kwargs['pk']
        )


class LimpiarCarritoView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        CarritoItem.objects.filter(usuario=request.user).delete()
        return Response({'mensaje': 'Carrito vaciado.'}, status=204)