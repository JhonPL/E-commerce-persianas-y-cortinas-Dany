import hashlib

from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import generics
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Factura
from .permissions import EsServicioInterno
from .pdf import build_demo_invoice_pdf
from .serializers import DemoInvoiceSerializer, FacturaSerializer


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


class DemoInvoicePdfView(APIView):
    permission_classes = [EsServicioInterno]

    def post(self, request):
        serializer = DemoInvoiceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        invoice_number = f"DEMO-{data['pedido_id']:06d}"
        demo_cufe = "DEMO-NO-FISCAL-" + hashlib.sha256(
            f"ACADEMIC-DEMO|{invoice_number}|{data['pedido_id']}".encode("utf-8")
        ).hexdigest().upper()
        details = [
            {
                **item,
                "ancho_cm": str(item["ancho_cm"]),
                "alto_cm": str(item["alto_cm"]),
                "precio_total": str(item["precio_total"]),
            }
            for item in data["detalles"]
        ]
        invoice, created = Factura.objects.get_or_create(
            pedido_id=data["pedido_id"],
            defaults={
                "numero_factura": invoice_number,
                "cufe": demo_cufe,
                "cliente_nombre": data["cliente_nombre"],
                "cliente_email": data["cliente_email"],
                "direccion": data["direccion"],
                "total": data["total"],
                "detalles": details,
                "enviada_dian": False,
                "estado": Factura.GENERADA,
            },
        )
        if not created and (
            invoice.total != data["total"]
            or invoice.detalles != details
            or invoice.cliente_email != data["cliente_email"]
        ):
            return Response(
                {"detail": "El pedido ya tiene un comprobante con otros datos."},
                status=status.HTTP_409_CONFLICT,
            )
        if not invoice.cufe:
            invoice.cufe = demo_cufe
            invoice.save(update_fields=["cufe"])

        pdf = build_demo_invoice_pdf(
            invoice_number=invoice.numero_factura,
            issued_at=invoice.fecha_emision or timezone.now(),
            data=data,
            cufe=demo_cufe,
        )
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = (
            f'attachment; filename="{invoice.numero_factura}.pdf"'
        )
        response["X-Invoice-Number"] = invoice.numero_factura
        return response
