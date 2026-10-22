import base64
import math
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from io import BytesIO

import qrcode
from django.conf import settings
from django.utils import timezone
from qrcode.image.svg import SvgPathImage


def _number_below_thousand(number):
    units = (
        "cero", "uno", "dos", "tres", "cuatro", "cinco", "seis", "siete",
        "ocho", "nueve", "diez", "once", "doce", "trece", "catorce",
        "quince", "dieciséis", "diecisiete", "dieciocho", "diecinueve",
        "veinte", "veintiuno", "veintidós", "veintitrés", "veinticuatro",
        "veinticinco", "veintiséis", "veintisiete", "veintiocho",
        "veintinueve",
    )
    tens = {
        3: "treinta", 4: "cuarenta", 5: "cincuenta", 6: "sesenta",
        7: "setenta", 8: "ochenta", 9: "noventa",
    }
    hundreds = {
        1: "ciento", 2: "doscientos", 3: "trescientos",
        4: "cuatrocientos", 5: "quinientos", 6: "seiscientos",
        7: "setecientos", 8: "ochocientos", 9: "novecientos",
    }
    if number < 30:
        return units[number]
    if number < 100:
        quotient, remainder = divmod(number, 10)
        return tens[quotient] if not remainder else (
            f"{tens[quotient]} y {units[remainder]}"
        )
    if number == 100:
        return "cien"
    quotient, remainder = divmod(number, 100)
    return hundreds[quotient] if not remainder else (
        f"{hundreds[quotient]} {_number_below_thousand(remainder)}"
    )


def _number_words(number):
    if number < 1000:
        return _number_below_thousand(number)
    if number < 1_000_000:
        thousands, remainder = divmod(number, 1000)
        prefix = "mil" if thousands == 1 else (
            f"{_number_below_thousand(thousands)} mil"
        )
        return prefix if not remainder else (
            f"{prefix} {_number_below_thousand(remainder)}"
        )
    millions, remainder = divmod(number, 1_000_000)
    prefix = "un millón" if millions == 1 else (
        f"{_number_below_thousand(millions)} millones"
    )
    return prefix if not remainder else f"{prefix} {_number_words(remainder)}"


def amount_in_words(value):
    whole = int(Decimal(value).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    words = _number_words(whole).replace("veintiuno", "veintiún")
    if words.endswith("uno"):
        words = f"{words[:-3]}un"
    return f"{words.capitalize()} pesos colombianos M/CTE."


def format_money(value):
    amount = f"{Decimal(value):,.0f}".replace(",", ".")
    return f"$ {amount}"


def _format_measurement(value):
    return f"{Decimal(value):.2f}".replace(".", ",")


def category_icon(category_name):
    value = str(category_name or "").casefold()
    if "accesorio" in value:
        return "icons/icon accesorio.png"
    if "cortina" in value:
        return "icons/icon cortina.png"
    if "persiana" in value:
        return "icons/inon persiana.png"
    return "icons/document-outline-regular.png"


def _description_parts(value, max_length=220):
    text = str(value or "").strip()
    if not text:
        return [""]

    parts = []
    while len(text) > max_length:
        split_at = text.rfind(" ", 0, max_length + 1)
        if split_at < max_length // 2:
            split_at = max_length
        parts.append(text[:split_at].strip())
        text = text[split_at:].strip()
    if text:
        parts.append(text)
    return parts


def _estimated_row_height(row):
    title_lines = max(1, math.ceil(len(row["producto_nombre"]) / 40))
    description_lines = math.ceil(len(row["display_description"]) / 40)
    specs_lines = math.ceil(len(row["display_specs"]) / 40)
    return max(
        75.5,
        15 + title_lines * 13.5 + (description_lines + specs_lines) * 14.2,
    )


def _paginate_invoice_rows(rows, *, max_height, max_rows):
    pages = []
    current_page = []
    current_height = 0
    for row in rows:
        row_height = _estimated_row_height(row)
        if current_page and (
            current_height + row_height > max_height
            or len(current_page) >= max_rows
        ):
            pages.append(current_page)
            current_page = []
            current_height = 0
        current_page.append(row)
        current_height += row_height
    if current_page:
        pages.append(current_page)
    return pages


def _demo_qr(invoice_number, pedido_id, issued_at):
    payload = (
        f"DEMO-NO-FISCAL|pedido={pedido_id}|documento={invoice_number}|"
        f"fecha={issued_at.isoformat()}"
    )
    image = qrcode.make(payload, image_factory=SvgPathImage)
    output = BytesIO()
    image.save(output)
    encoded = base64.b64encode(output.getvalue()).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"


def _format_date(value):
    if not value:
        return ""
    if isinstance(value, datetime):
        value = timezone.localtime(value)
    if isinstance(value, (date, datetime)):
        return value.strftime("%d/%m/%Y")
    return ""


def build_invoice_context(*, invoice, data, issued_at):
    details = []
    invoice_rows = []
    for item in data["detalles"]:
        quantity = item["cantidad"]
        line_total = Decimal(item["precio_total"])
        detail = {
            **item,
            "unit_price": line_total / quantity,
            "line_total": line_total,
            "formatted_unit_price": format_money(line_total / quantity),
            "formatted_line_total": format_money(line_total),
            "icon": category_icon(item.get("categoria_nombre")),
        }
        details.append(detail)

        description_parts = _description_parts(item.get("descripcion"))
        for part_index, description_part in enumerate(description_parts):
            specs = []
            if not part_index:
                specs.append(
                    "Medidas: "
                    f"{_format_measurement(item['ancho_cm'])} × "
                    f"{_format_measurement(item['alto_cm'])} cm"
                )
                if item.get("material"):
                    specs.append(f"Material: {item['material']}")
                if item.get("color"):
                    specs.append(f"Color: {item['color']}")
                if item.get("tipo_instalacion"):
                    specs.append(f"Instalación: {item['tipo_instalacion']}")
            invoice_rows.append({
                **detail,
                "display_description": description_part,
                "display_specs": " · ".join(specs),
                "is_continuation": part_index > 0,
                "formatted_unit_price": (
                    "" if part_index else detail["formatted_unit_price"]
                ),
                "formatted_line_total": (
                    "" if part_index else detail["formatted_line_total"]
                ),
                "display_quantity": "" if part_index else quantity,
            })

    total = Decimal(data["total"])
    subtotal = sum(
        (item["line_total"] for item in details),
        Decimal("0.00"),
    )
    invoice_pages = _paginate_invoice_rows(
        invoice_rows,
        max_height=275,
        max_rows=3,
    )
    continuation_pages = _paginate_invoice_rows(
        [
            row
            for page_rows in invoice_pages[1:]
            for row in page_rows
        ],
        max_height=600,
        max_rows=7,
    )
    issuer = {
        "name": "Persianas & Cortinas Dany",
        "identification": settings.INVOICE_ISSUER_NIT,
        "address": settings.INVOICE_ISSUER_ADDRESS,
        "phone": settings.INVOICE_ISSUER_PHONE,
        "email": settings.INVOICE_ISSUER_EMAIL,
        "website": getattr(settings, "INVOICE_ISSUER_WEBSITE", ""),
    }
    customer = {
        "name": data["cliente_nombre"],
        "identification": data.get("identificacion", ""),
        "address": data.get("direccion", ""),
        "phone": data.get("telefono", ""),
        "email": data.get("cliente_email", ""),
        "recipient": data.get("nombre_recibe", ""),
    }
    return {
        "invoice": {
            "number": invoice.numero_factura,
            "order_number": data["pedido_id"],
            "cufe": invoice.cufe,
            "issued_at": issued_at,
            "issued_date": _format_date(issued_at),
            "issued_date_spaced": " / ".join(_format_date(issued_at).split("/")),
            "due_date": _format_date(data.get("fecha_vencimiento")),
            "operation_type": "Venta de productos",
            "currency": "COP - Peso Colombiano",
            "generated_at": timezone.localtime(issued_at),
            "qr_data_uri": _demo_qr(
                invoice.numero_factura,
                data["pedido_id"],
                issued_at,
            ),
        },
        "issuer": issuer,
        "customer": customer,
        "details": details,
        "subtotal": subtotal,
        "formatted_subtotal": format_money(subtotal),
        "total": total,
        "formatted_total": format_money(total),
        "total_in_words": amount_in_words(total),
        "first_page_details": invoice_pages[0],
        "continuation_pages": continuation_pages,
        "paid": data.get("importe_pagado"),
        "formatted_paid": (
            format_money(data["importe_pagado"])
            if data.get("importe_pagado") is not None
            else None
        ),
        "balance": data.get("saldo_pendiente"),
        "formatted_balance": (
            format_money(data["saldo_pendiente"])
            if data.get("saldo_pendiente") is not None
            else None
        ),
        "payment_method": data.get("metodo_pago", ""),
        "payment_status": data.get("estado_pago", ""),
        "order_status": data.get("estado_pedido", ""),
        "observations": data.get("observaciones", ""),
    }
