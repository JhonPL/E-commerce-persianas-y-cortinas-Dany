import json
import re
import tempfile
from datetime import date, datetime, timezone
from io import StringIO
from pathlib import Path

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Factura
from .pdf import _styles


@override_settings(INTERNAL_SERVICE_TOKEN="internal-test-token")
class BillingServiceApiTests(APITestCase):
    def setUp(self):
        self.payload = {
            "pedido_id": 45,
            "numero_factura": "FAC-45",
            "cufe": "cufe-45",
            "xml_path": "https://files.example.com/factura.xml",
            "pdf_path": "https://files.example.com/factura.pdf",
            "enviada_dian": False,
            "estado": Factura.GENERADA,
            "fecha_vencimiento": "2026-12-31",
        }

    def _post(self):
        return self.client.post(
            "/api/internal/facturas/",
            self.payload,
            format="json",
            HTTP_X_INTERNAL_SERVICE_TOKEN="internal-test-token",
        )

    def test_api_requires_internal_service_token(self):
        response = self.client.post(
            "/api/internal/facturas/",
            self.payload,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(Factura.objects.exists())

    def test_create_and_retrieve_invoice_by_order_id(self):
        created = self._post()
        retrieved = self.client.get(
            "/api/internal/facturas/pedido/45/",
            HTTP_X_INTERNAL_SERVICE_TOKEN="internal-test-token",
        )

        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        self.assertEqual(created.data["pedido_id"], 45)
        self.assertEqual(retrieved.status_code, status.HTTP_200_OK)
        self.assertEqual(retrieved.data["numero_factura"], "FAC-45")

    def test_duplicate_invoice_for_order_is_rejected(self):
        self.assertEqual(self._post().status_code, status.HTTP_201_CREATED)
        duplicate = self._post()
        self.assertEqual(duplicate.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Factura.objects.count(), 1)

    def test_status_and_dian_fields_can_be_updated_without_transmission_logic(self):
        self._post()
        response = self.client.patch(
            "/api/internal/facturas/pedido/45/",
            {"estado": Factura.TRANSMITIDA, "enviada_dian": True},
            format="json",
            HTTP_X_INTERNAL_SERVICE_TOKEN="internal-test-token",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["estado"], Factura.TRANSMITIDA)


class InvoiceTransferTests(APITestCase):
    def test_import_preserves_invoice_and_order_ids(self):
        issued_at = datetime(2024, 1, 2, tzinfo=timezone.utc).isoformat()
        payload = {
            "facturas": [
                {
                    "factura_id": 9,
                    "pedido_id": 45,
                    "numero_factura": "FAC-45",
                    "cufe": "cufe-45",
                    "xml_path": None,
                    "pdf_path": None,
                    "enviada_dian": False,
                    "estado": Factura.GENERADA,
                    "fecha_emision": issued_at,
                    "fecha_vencimiento": "2024-02-02",
                }
            ]
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "invoices.json"
            source.write_text(json.dumps(payload), encoding="utf-8")
            call_command("import_invoices", source, stdout=StringIO())

        invoice = Factura.objects.get(pk=9)
        self.assertEqual(invoice.pedido_id, 45)
        self.assertEqual(invoice.cufe, "cufe-45")
        self.assertEqual(invoice.fecha_emision.isoformat(), issued_at)
        self.assertEqual(invoice.fecha_vencimiento, date(2024, 2, 2))

    def test_import_refuses_nonempty_database(self):
        Factura.objects.create(
            pedido_id=1,
            numero_factura="FAC-1",
            cufe="cufe-1",
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "invoices.json"
            source.write_text(json.dumps({"facturas": []}), encoding="utf-8")
            with self.assertRaisesMessage(
                CommandError,
                "La base de facturación no está vacía; se canceló la importación.",
            ):
                call_command("import_invoices", source)


@override_settings(INTERNAL_SERVICE_TOKEN="internal-test-token")
class DemoInvoicePdfTests(APITestCase):
    def setUp(self):
        self.payload = {
            "pedido_id": 81,
            "cliente_nombre": "Cliente de prueba",
            "cliente_email": "cliente@example.test",
            "direccion": "Calle 10, Villavicencio",
            "total": "125000.00",
            "detalles": [
                {
                    "producto_id": 12,
                    "producto_nombre": "Cortina Blackout",
                    "categoria_nombre": "Cortinas",
                    "descripcion": "Tela de bloqueo de luz",
                    "cantidad": 1,
                    "ancho_cm": "100.00",
                    "alto_cm": "200.00",
                    "precio_total": "125000.00",
                }
            ],
        }

    def _post(self, payload=None, **headers):
        return self.client.post(
            "/api/internal/facturas/demo-pdf/",
            payload or self.payload,
            format="json",
            **headers,
        )

    def test_invoice_text_styles_use_a_consistent_font_size(self):
        self.assertEqual(
            {style.fontSize for style in _styles().values()},
            {7.5},
        )

    def test_generates_and_records_a_demo_pdf_once_per_order(self):
        headers = {"HTTP_X_INTERNAL_SERVICE_TOKEN": "internal-test-token"}
        first = self._post(**headers)
        second = self._post(**headers)

        self.assertEqual(first.status_code, status.HTTP_200_OK)
        self.assertEqual(first["Content-Type"], "application/pdf")
        self.assertEqual(first["X-Invoice-Number"], "DEMO-000081")
        self.assertTrue(first.content.startswith(b"%PDF-"))
        self.assertEqual(second.status_code, status.HTTP_200_OK)
        self.assertEqual(Factura.objects.count(), 1)
        invoice = Factura.objects.get(pedido_id=81)
        self.assertTrue(invoice.cufe.startswith("DEMO-NO-FISCAL-"))
        self.assertFalse(invoice.enviada_dian)
        self.assertIn(b"cobro real", first.content)
        self.assertIn(b"FACTURA", first.content)
        self.assertIn(b"DEMO-NO-FISCAL", first.content)
        self.assertIn(b"QR DEMOSTRACI", first.content)

    def test_pdf_renders_mixed_product_categories_on_a4_with_original_logo(self):
        self.payload["detalles"].append(
            {
                "producto_id": 13,
                "producto_nombre": "Persiana enrollable",
                "categoria_nombre": "Persianas",
                "descripcion": "Sistema manual",
                "cantidad": 2,
                "ancho_cm": "125.00",
                "alto_cm": "180.00",
                "precio_total": "250000.00",
            }
        )
        self.payload["total"] = "375000.00"
        response = self._post(
            self.payload,
            HTTP_X_INTERNAL_SERVICE_TOKEN="internal-test-token",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.content.startswith(b"%PDF-"))
        self.assertIn(b"cobro real", response.content)
        self.assertGreater(response.content.count(b"/Subtype /Image"), 0)
        icon_dir = Path(__file__).parent / "assets" / "icons"
        for icon_name in (
            "blind-outline-regular",
            "curtain-outline-regular",
            "drill-outline-regular",
        ):
            self.assertTrue((icon_dir / f"{icon_name}.svg").is_file())
            self.assertTrue((icon_dir / f"{icon_name}.png").is_file())

    def test_pdf_splits_many_products_and_long_descriptions_across_pages(self):
        details = [
            {
                "producto_id": product_id,
                "producto_nombre": f"Producto personalizado {product_id}",
                "categoria_nombre": "Accesorios" if product_id % 3 == 0 else "Persianas",
                "descripcion": (
                    "Descripción extensa con detalles de acabados y medidas. " * 80
                    if product_id == 1
                    else "Producto a medida."
                ),
                "cantidad": 1,
                "ancho_cm": "100.00",
                "alto_cm": "200.00",
                "precio_total": "1000.00",
            }
            for product_id in range(1, 31)
        ]
        payload = {
            **self.payload,
            "detalles": details,
            "total": "30000.00",
        }
        response = self._post(
            payload,
            HTTP_X_INTERNAL_SERVICE_TOKEN="internal-test-token",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        page_count = len(re.findall(rb"/Type /Page\b", response.content))
        self.assertGreater(page_count, 1)

    def test_rejects_invoice_when_item_total_does_not_match(self):
        payload = {**self.payload, "total": "126000.00"}
        response = self._post(
            payload,
            HTTP_X_INTERNAL_SERVICE_TOKEN="internal-test-token",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Factura.objects.exists())

    def test_pdf_generation_requires_internal_service_token(self):
        response = self._post()

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(Factura.objects.exists())
