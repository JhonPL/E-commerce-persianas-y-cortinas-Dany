import json
import tempfile
from datetime import date, datetime, timezone
from io import StringIO
from pathlib import Path
from unittest import skipUnless

from django.core.management import call_command
from django.core.management.base import CommandError
from django.template.loader import render_to_string
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from .invoice_data import build_invoice_context, category_icon
from .models import Factura
from .pdf import render_invoice_document

try:
    import weasyprint  # noqa: F401
except OSError:
    WEASYPRINT_AVAILABLE = False
else:
    WEASYPRINT_AVAILABLE = True


def _find_element_box(page, class_name):
    pending = [page._page_box]
    while pending:
        box = pending.pop()
        element = getattr(box, "element", None)
        if element is not None and class_name in element.get("class", "").split():
            return box
        pending.extend(reversed(getattr(box, "children", [])))
    raise AssertionError(f"No se encontró el elemento .{class_name} en la página.")


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
            "fecha_vencimiento": "2026-11-20",
            "total": "125000.00",
            "detalles": [
                {
                    "producto_id": 12,
                    "producto_nombre": "Cortina Blackout",
                    "categoria_nombre": "Cortinas",
                    "descripcion": "Tela de bloqueo de luz",
                    "material": "Lino",
                    "color": "Marfil",
                    "tipo_instalacion": "Pared",
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

    @skipUnless(
        WEASYPRINT_AVAILABLE,
        "WeasyPrint native libraries (Pango/GTK) are unavailable in this environment.",
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
        self.assertGreater(first.content.count(b"/Subtype /Image"), 0)

    def test_category_icon_uses_the_product_category(self):
        self.assertEqual(
            category_icon("Persianas"),
            "icons/inon persiana.png",
        )
        self.assertEqual(
            category_icon("Cortinas"),
            "icons/icon cortina.png",
        )
        self.assertEqual(
            category_icon("Accesorios"),
            "icons/icon accesorio.png",
        )
        self.assertEqual(
            category_icon("Otra categoría"),
            "icons/document-outline-regular.png",
        )

    def test_prepared_context_has_local_icons_and_demo_qr(self):
        invoice = Factura(
            pedido_id=81,
            numero_factura="DEMO-000081",
            cufe="DEMO-NO-FISCAL-TEST",
        )
        context = build_invoice_context(
            invoice=invoice,
            issued_at=datetime(2026, 10, 21, 12, 0, tzinfo=timezone.utc),
            data={
                **self.payload,
                "fecha_vencimiento": date(2026, 11, 20),
            },
        )

        self.assertEqual(context["formatted_total"], "$ 125.000")
        self.assertEqual(context["invoice"]["due_date"], "20/11/2026")
        self.assertIn("Ciento veinticinco mil", context["total_in_words"])
        self.assertTrue(
            context["invoice"]["qr_data_uri"].startswith("data:image/svg+xml;base64,")
        )
        self.assertEqual(
            context["details"][0]["icon"],
            "icons/icon cortina.png",
        )
        self.assertEqual(context["details"][0]["material"], "Lino")
        self.assertEqual(context["details"][0]["color"], "Marfil")
        self.assertEqual(context["details"][0]["tipo_instalacion"], "Pared")
        self.assertEqual(context["first_page_details"][0]["display_quantity"], 1)
        self.assertIn(
            "Medidas: 100,00 × 200,00 cm",
            context["first_page_details"][0]["display_specs"],
        )
        self.assertEqual(context["invoice"]["order_number"], 81)
        self.assertEqual(
            context["issuer"],
            {
                "name": "Persianas & Cortinas Dany",
                "identification": "1.122.507.213-3",
                "address": "Cra. 13 # 20 - 52, Granada, Meta",
                "phone": "312 355 8218",
                "email": "percortinasdany@gmail.com",
                "website": "",
            },
        )
        html = render_to_string("facturacion/invoice.html", context)
        totals = html.split('<div class="tot">', 1)[1].split("</div>", 1)[0]
        self.assertIn(
            '<tr class="final"><td>TOTAL A PAGAR</td><td>$ 125.000</td></tr>',
            totals,
        )
        self.assertNotIn("SUBTOTAL", totals)
        self.assertNotIn("SALDO PENDIENTE", totals)

    def test_resource_fetcher_rejects_external_urls(self):
        from .pdf import _invoice_url_fetcher

        with self.assertRaisesMessage(
            ValueError,
            "La factura solo puede cargar recursos locales.",
        ):
            _invoice_url_fetcher("https://example.com/logo.png")

    @skipUnless(
        WEASYPRINT_AVAILABLE,
        "WeasyPrint native libraries (Pango/GTK) are unavailable in this environment.",
    )
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
        self.assertGreater(response.content.count(b"/Subtype /Image"), 0)
        invoice = Factura.objects.get(pedido_id=81)
        context = build_invoice_context(
            invoice=invoice,
            issued_at=invoice.fecha_emision,
            data=self.payload,
        )
        page = render_invoice_document(context).pages[0]
        self.assertAlmostEqual(page.width, 793.70, places=1)
        self.assertAlmostEqual(page.height, 1122.52, places=1)
        assets_dir = Path(__file__).parent / "assets"
        self.assertTrue((assets_dir / "logogreen-reference.png").is_file())
        for icon_name in (
            "inon persiana.png",
            "icon cortina.png",
            "icon accesorio.png",
        ):
            self.assertTrue((assets_dir / "icons" / icon_name).is_file())
        for font_name in (
            "Montserrat-400.woff2",
            "Montserrat-500.woff2",
            "Montserrat-600.woff2",
            "Montserrat-700.woff2",
            "Montserrat-800.woff2",
            "Script-400.woff2",
        ):
            self.assertTrue((assets_dir / "fonts" / font_name).is_file())

    @skipUnless(
        WEASYPRINT_AVAILABLE,
        "WeasyPrint native libraries (Pango/GTK) are unavailable in this environment.",
    )
    def test_footer_stays_near_the_color_bar_with_one_or_two_products(self):
        issued_at = datetime(2026, 10, 21, 12, 0, tzinfo=timezone.utc)
        page_footer_positions = []
        for details in (
            self.payload["detalles"],
            [
                *self.payload["detalles"],
                {
                    **self.payload["detalles"][0],
                    "producto_id": 13,
                    "producto_nombre": "Persiana enrollable",
                    "categoria_nombre": "Persianas",
                    "descripcion": "Sistema manual",
                    "precio_total": "250000.00",
                },
            ],
        ):
            payload = {
                **self.payload,
                "detalles": details,
                "total": str(sum(
                    (int(item["precio_total"].split(".")[0]) for item in details),
                    0,
                )) + ".00",
            }
            context = build_invoice_context(
                invoice=Factura(
                    pedido_id=81,
                    numero_factura="DEMO-000081",
                    cufe="DEMO-NO-FISCAL-81",
                ),
                issued_at=issued_at,
                data=payload,
            )
            document = render_invoice_document(context)
            self.assertEqual(len(document.pages), 1)
            page = document.pages[0]
            footer = _find_element_box(page, "foot")
            color_bar = _find_element_box(page, "bar")
            self.assertGreater(footer.position_y, 950)
            self.assertLess(
                footer.position_y + footer.height,
                color_bar.position_y,
            )
            page_footer_positions.append(footer.position_y)

        self.assertAlmostEqual(
            page_footer_positions[0],
            page_footer_positions[1],
            places=1,
        )

    @skipUnless(
        WEASYPRINT_AVAILABLE,
        "WeasyPrint native libraries (Pango/GTK) are unavailable in this environment.",
    )
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
        invoice = Factura.objects.get(pedido_id=81)
        context = build_invoice_context(
            invoice=invoice,
            issued_at=invoice.fecha_emision,
            data=payload,
        )
        self.assertEqual(len(context["first_page_details"]), 2)
        self.assertGreater(len(context["continuation_pages"]), 1)
        prepared_rows = context["first_page_details"] + [
            row
            for page_details in context["continuation_pages"]
            for row in page_details
        ]
        long_description_parts = [
            row["display_description"]
            for row in prepared_rows
            if row["producto_id"] == 1 and row["display_description"]
        ]
        self.assertEqual(
            " ".join(long_description_parts),
            details[0]["descripcion"].strip(),
        )
        self.assertEqual(
            {row["producto_id"] for row in prepared_rows},
            {detail["producto_id"] for detail in details},
        )
        document = render_invoice_document(context)
        self.assertGreater(len(document.pages), 1)
        footer = _find_element_box(document.pages[0], "foot")
        information_cards = _find_element_box(document.pages[0], "info")
        color_bar = _find_element_box(document.pages[0], "bar")
        self.assertGreater(
            footer.position_y,
            information_cards.position_y + information_cards.height,
        )
        self.assertLess(
            footer.position_y + footer.height,
            color_bar.position_y,
        )

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
