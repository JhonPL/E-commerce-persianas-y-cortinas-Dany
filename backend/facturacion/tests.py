import json
import tempfile
from datetime import date, datetime, timezone
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from django.core.management import call_command
from django.test import SimpleTestCase

from facturacion.models import Factura


class InvoiceExportTests(SimpleTestCase):
    @patch(
        "facturacion.management.commands.export_invoices."
        "Factura.objects.order_by"
    )
    def test_export_preserves_invoice_id_and_order_reference(self, order_by):
        order_by.return_value.values.return_value = [
            {
                "factura_id": 9,
                "pedido_id": 45,
                "numero_factura": "FAC-45",
                "cufe": "cufe-45",
                "xml_path": None,
                "pdf_path": None,
                "enviada_dian": False,
                "estado": "generada",
                "fecha_emision": datetime(2024, 1, 2, tzinfo=timezone.utc),
                "fecha_vencimiento": date(2024, 2, 2),
            }
        ]
        with tempfile.TemporaryDirectory() as temp_dir:
            destination = Path(temp_dir) / "invoices.json"
            call_command(
                "export_invoices",
                "--file",
                destination,
                stdout=StringIO(),
            )
            exported = json.loads(destination.read_text(encoding="utf-8"))

        self.assertEqual(exported["facturas"][0]["factura_id"], 9)
        self.assertEqual(exported["facturas"][0]["pedido_id"], 45)
