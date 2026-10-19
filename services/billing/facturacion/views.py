from django.shortcuts import get_object_or_404
from rest_framework import generics

from .models import Factura
from .permissions import EsServicioInterno
from .serializers import FacturaSerializer


class FacturaListCreateView(generics.ListCreateAPIView):
    queryset = Factura.objects.all()
    serializer_class = FacturaSerializer
    permission_classes = [EsServicioInterno]


class FacturaDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = FacturaSerializer
    permission_classes = [EsServicioInterno]
    lookup_url_kwarg = "pedido_id"
    http_method_names = ["get", "patch", "head", "options"]

    def get_object(self):
        return get_object_or_404(Factura, pedido_id=self.kwargs["pedido_id"])
