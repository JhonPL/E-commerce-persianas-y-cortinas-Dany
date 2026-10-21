from decimal import Decimal, ROUND_HALF_UP
from html import escape
from io import BytesIO
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.graphics import renderPDF
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing
from reportlab.platypus import (
    Flowable,
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from django.conf import settings


GREEN = colors.HexColor("#8FC263")
LIGHT_GREEN = colors.HexColor("#CFE795")
BEIGE = colors.HexColor("#F7EFD3")
BLACK = colors.HexColor("#000000")
WHITE = colors.white
PALE = colors.HexColor("#F8FAF5")
LINE = colors.HexColor("#D8E4CB")
MUTED = colors.HexColor("#596158")
PAGE_WIDTH, _ = A4
PAGE_MARGIN = 10 * mm
CONTENT_WIDTH = PAGE_WIDTH - (2 * PAGE_MARGIN)
LOGO_PATH = Path(__file__).resolve().parent / "assets" / "logogreen.webp"
ICON_DIR = Path(__file__).resolve().parent / "assets" / "icons"

PRODUCT_ICON_PATHS = {
    "persiana": ICON_DIR / "blind-outline-regular.png",
    "cortina": ICON_DIR / "curtain-outline-regular.png",
    "accesorio": ICON_DIR / "drill-outline-regular.png",
}


def _money(value):
    amount = f"{Decimal(value):,.0f}".replace(",", ".")
    return f"$ {amount}"


def _escape(value):
    return escape(str(value or ""))


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
        return tens[quotient] if not remainder else f"{tens[quotient]} y {units[remainder]}"
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
    return prefix if not remainder else (
        f"{prefix} {_number_words(remainder)}"
    )


def _amount_in_words(value):
    whole = int(Decimal(value).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    words = _number_words(whole)
    words = words.replace("veintiuno", "veintiún")
    if words.endswith("uno"):
        words = f"{words[:-3]}un"
    return f"{words.capitalize()} pesos colombianos M/CTE."


def _category(item):
    value = str(item.get("categoria_nombre") or "").casefold()
    if "cortina" in value:
        return "cortina"
    if "accesorio" in value:
        return "accesorio"
    return "persiana"


def _icon(name, size=5 * mm, white=False):
    suffix = "-white" if white else ""
    icon_path = ICON_DIR / f"{name}{suffix}.png"
    if not icon_path.is_file():
        raise FileNotFoundError(f"No se encontró el icono local de la factura: {icon_path}")
    return Image(str(icon_path), width=size, height=size)


class BadgeIcon(Flowable):
    def __init__(self, name, size=11 * mm):
        super().__init__()
        self.name = name
        self.width = size
        self.height = size

    def draw(self):
        canvas = self.canv
        canvas.saveState()
        canvas.setFillColor(GREEN)
        canvas.circle(self.width / 2, self.height / 2, self.width / 2, fill=1, stroke=0)
        icon_path = ICON_DIR / f"{self.name}-white.png"
        if not icon_path.is_file():
            raise FileNotFoundError(f"No se encontró el icono local de la factura: {icon_path}")
        inset = self.width * 0.25
        canvas.drawImage(
            str(icon_path),
            inset,
            inset,
            width=self.width - 2 * inset,
            height=self.height - 2 * inset,
            preserveAspectRatio=True,
            mask="auto",
        )
        canvas.restoreState()


class DemoQrCode(Flowable):
    def __init__(self, value, size=21 * mm):
        super().__init__()
        self.value = value
        self.width = size
        self.height = size

    def draw(self):
        qr = QrCodeWidget(self.value, barLevel="M")
        left, bottom, right, top = qr.getBounds()
        scale = min(self.width / (right - left), self.height / (top - bottom))
        drawing = Drawing(self.width, self.height)
        drawing.add(qr, name="qr")
        drawing.scale(scale, scale)
        renderPDF.draw(drawing, self.canv, 0, 0)


def _styles():
    base = getSampleStyleSheet()
    return {
        "brand": ParagraphStyle(
            "InvoiceBrand", parent=base["Normal"], fontName="Helvetica-Bold",
            fontSize=7.5, leading=10, textColor=BLACK,
        ),
        "brand_green": ParagraphStyle(
            "InvoiceBrandGreen", parent=base["Normal"], fontName="Helvetica-Bold",
            fontSize=7.5, leading=10, textColor=GREEN,
        ),
        "tagline": ParagraphStyle(
            "InvoiceTagline", parent=base["Normal"], fontName="Helvetica",
            fontSize=7.5, leading=10, textColor=BLACK,
        ),
        "title": ParagraphStyle(
            "InvoiceTitle", parent=base["Normal"], fontName="Helvetica-Bold",
            fontSize=7.5, leading=10, textColor=BLACK,
        ),
        "heading": ParagraphStyle(
            "InvoiceHeading", parent=base["Normal"], fontName="Helvetica-Bold",
            fontSize=7.5, leading=10, textColor=colors.HexColor("#659C3D"),
        ),
        "body": ParagraphStyle(
            "InvoiceBody", parent=base["Normal"], fontName="Helvetica",
            fontSize=7.5, leading=10, textColor=BLACK, wordWrap="CJK",
        ),
        "body_bold": ParagraphStyle(
            "InvoiceBodyBold", parent=base["Normal"], fontName="Helvetica-Bold",
            fontSize=7.5, leading=10, textColor=BLACK, wordWrap="CJK",
        ),
        "small": ParagraphStyle(
            "InvoiceSmall", parent=base["Normal"], fontName="Helvetica",
            fontSize=7.5, leading=10, textColor=MUTED, wordWrap="CJK",
        ),
        "table_header": ParagraphStyle(
            "InvoiceTableHeader", parent=base["Normal"], fontName="Helvetica-Bold",
            fontSize=7.5, leading=9, alignment=TA_CENTER, textColor=BLACK,
        ),
        "center": ParagraphStyle(
            "InvoiceCenter", parent=base["Normal"], fontName="Helvetica",
            fontSize=7.5, leading=10, alignment=TA_CENTER, textColor=BLACK,
        ),
        "right": ParagraphStyle(
            "InvoiceRight", parent=base["Normal"], fontName="Helvetica",
            fontSize=7.5, leading=10, alignment=TA_RIGHT, textColor=BLACK,
        ),
        "total": ParagraphStyle(
            "InvoiceTotal", parent=base["Normal"], fontName="Helvetica-Bold",
            fontSize=7.5, leading=10, textColor=BLACK,
        ),
    }


def _page_decoration(canvas, document):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#659C3D"))
    canvas.setLineWidth(0.8)
    canvas.line(PAGE_MARGIN, 8 * mm, PAGE_WIDTH - PAGE_MARGIN, 8 * mm)
    segment_width = CONTENT_WIDTH / 5
    for index, color in enumerate((BLACK, GREEN, colors.HexColor("#76A746"), LIGHT_GREEN, BEIGE)):
        canvas.setFillColor(color)
        canvas.rect(PAGE_MARGIN + index * segment_width, 0, segment_width, 4 * mm, fill=1, stroke=0)
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(MUTED)
    canvas.drawRightString(
        PAGE_WIDTH - PAGE_MARGIN,
        5 * mm,
        f"Documento académico de demostración · Página {document.page}",
    )
    canvas.restoreState()


def _party_block(title, name, lines, styles):
    content = [Paragraph(title, styles["heading"]), Spacer(1, 1.5 * mm)]
    rows = [
        [_icon("user-outline-regular", 4 * mm), Paragraph(f"<b>{_escape(name)}</b>", styles["body"])]
    ]
    icon_names = {
        "Identificación": "document-outline-regular",
        "Dirección": "location-outline-regular",
        "Teléfono": "phone-call",
        "Correo": "mail-outline-regular",
        "Recibe": "user-outline-regular",
    }
    rows.extend(
        [
            _icon(icon_names.get(label, "document-outline-regular"), 3.5 * mm),
            Paragraph(f"{_escape(label)}: {_escape(value)}", styles["body"]),
        ]
        for label, value in lines
        if value
    )
    content.append(Table(
        rows,
        colWidths=[6 * mm, (CONTENT_WIDTH / 2) - 25 * mm],
        style=TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 2),
            ("TOPPADDING", (0, 0), (-1, -1), 1),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        ]),
    ))
    table = Table(
        [[content]],
        colWidths=[(CONTENT_WIDTH / 2) - 3 * mm],
    )
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BEIGE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    return table


def _item_description(item, styles):
    parts = [f"<b>{_escape(item['producto_nombre'])}</b>"]
    category = item.get("categoria_nombre")
    if category:
        parts.append(f"<font color='#659C3D'>{_escape(category)}</font>")
    description = item.get("descripcion")
    if description:
        parts.append(_escape(description))
    parts.append(
        f"<font color='#596158'>Medidas: {_escape(item['ancho_cm'])} × "
        f"{_escape(item['alto_cm'])} cm</font>"
    )
    for label, key in (("Material", "material"), ("Color", "color")):
        if item.get(key):
            parts.append(f"<font color='#596158'>{label}: {_escape(item[key])}</font>")
    return Paragraph("<br/>".join(parts), styles["body"])


def _product_table(data, styles):
    rows = [[
        "",
        Paragraph("DESCRIPCIÓN", styles["table_header"]),
        Paragraph("CANT.", styles["table_header"]),
        Paragraph("VALOR UNITARIO", styles["table_header"]),
        Paragraph("TOTAL", styles["table_header"]),
    ]]
    for item in data["detalles"]:
        quantity = item["cantidad"]
        unit_price = (
            Decimal(item["precio_total"]) / quantity
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        rows.append([
            Image(
                str(PRODUCT_ICON_PATHS[_category(item)]),
                width=14 * mm,
                height=14 * mm,
            ),
            _item_description(item, styles),
            Paragraph(str(quantity), styles["center"]),
            Paragraph(_money(unit_price), styles["right"]),
            Paragraph(f"<b>{_money(item['precio_total'])}</b>", styles["right"]),
        ])
    table = Table(
        rows,
        colWidths=[20 * mm, 83 * mm, 16 * mm, 34 * mm, CONTENT_WIDTH - 153 * mm],
        repeatRows=1,
        splitInRow=1,
        hAlign="LEFT",
    )
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), GREEN),
        ("BACKGROUND", (0, 1), (-1, -1), WHITE),
        ("GRID", (0, 0), (-1, -1), 0.45, LINE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("ALIGN", (2, 1), (2, -1), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return table


def _summary(data, styles):
    subtotal = sum(
        (Decimal(item["precio_total"]) for item in data["detalles"]),
        Decimal("0.00"),
    )
    summary_rows = [
        [Paragraph("SUBTOTAL", styles["body_bold"]), Paragraph(_money(subtotal), styles["right"])],
    ]
    paid = data.get("importe_pagado")
    balance = data.get("saldo_pendiente")
    if paid is not None:
        summary_rows.append([
            Paragraph("PAGADO (SIMULACIÓN)", styles["body"]),
            Paragraph(_money(paid), styles["right"]),
        ])
    if balance is not None:
        summary_rows.append([
            Paragraph("SALDO PENDIENTE", styles["body"]),
            Paragraph(_money(balance), styles["right"]),
        ])
    summary_rows.append([
        Paragraph("TOTAL A PAGAR", styles["total"]),
        Paragraph(_money(data["total"]), styles["total"]),
    ])
    totals = Table(summary_rows, colWidths=[55 * mm, 31 * mm], hAlign="RIGHT")
    totals.setStyle(TableStyle([
        ("LINEABOVE", (0, 0), (-1, -1), 0.5, LINE),
        ("LINEBELOW", (0, 0), (-1, -2), 0.45, LINE),
        ("BACKGROUND", (0, -1), (-1, -1), LIGHT_GREEN),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    words = Table(
        [[
            Paragraph(
                f"<b>SON:</b><br/>{_escape(_amount_in_words(data['total']))}",
                styles["body"],
            )
        ]],
        colWidths=[CONTENT_WIDTH - 91 * mm],
    )
    words.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PALE),
        ("BOX", (0, 0), (-1, -1), 0.45, LINE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    row = Table([[words, totals]], colWidths=[CONTENT_WIDTH - 91 * mm, 91 * mm])
    row.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return row


def _info_card(title, text, icon_name, styles, background=PALE):
    card = Table(
        [
            [BadgeIcon(icon_name, 9 * mm), Paragraph(f"<b>{_escape(title.upper())}</b>", styles["heading"])],
            ["", Paragraph(text, styles["body"])],
        ],
        colWidths=[11 * mm, CONTENT_WIDTH / 3 - 23 * mm],
    )
    card.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), background),
        ("BOX", (0, 0), (-1, -1), 0.4, LINE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("SPAN", (0, 0), (0, -1)),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    return card


def build_demo_invoice_pdf(*, invoice_number, issued_at, data, cufe):
    if not LOGO_PATH.is_file():
        raise FileNotFoundError(f"No se encontró el logo original del negocio: {LOGO_PATH}")

    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=PAGE_MARGIN,
        leftMargin=PAGE_MARGIN,
        topMargin=9 * mm,
        bottomMargin=13 * mm,
        pageCompression=0,
        title=f"Factura de demostración {invoice_number}",
        author="Persianas & Cortinas Dany",
    )
    styles = _styles()
    story = []

    logo = Image(str(LOGO_PATH), width=30 * mm, height=30 * mm)
    brand = [
        Paragraph("PERSIANAS &amp; CORTINAS", styles["brand"]),
        Paragraph("DANY", styles["brand_green"]),
        Paragraph("Diseño, elegancia y confort<br/>para tus espacios", styles["tagline"]),
    ]
    invoice_details = [
        Paragraph("FACTURA", styles["title"]),
        Paragraph(
            f"<b>{_escape(invoice_number)}</b><br/>"
            "Documento de demostración académica<br/>"
            f"Fecha de emisión: {issued_at.strftime('%d/%m/%Y')}<br/>"
            f"Hora de generación: {issued_at.strftime('%H:%M')}<br/>"
            + (
                f"Fecha de vencimiento: {data['fecha_vencimiento'].strftime('%d/%m/%Y')}<br/>"
                if data.get("fecha_vencimiento")
                else ""
            )
            + "Moneda: COP - Peso colombiano",
            styles["body"],
        ),
    ]
    header = Table([[logo, brand, invoice_details]], colWidths=[40 * mm, 72 * mm, CONTENT_WIDTH - 112 * mm])
    header.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (2, 0), (2, 0), "LEFT"),
        ("LINEBELOW", (0, 0), (-1, -1), 1, GREEN),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.extend([header, Spacer(1, 5 * mm)])

    issuer_lines = [
        ("Identificación", "Datos de demostración académica"),
        ("Dirección", "Datos de demostración académica"),
    ]
    if settings.INVOICE_ISSUER_ADDRESS:
        issuer_lines[1] = ("Dirección", settings.INVOICE_ISSUER_ADDRESS)
    if settings.INVOICE_ISSUER_PHONE:
        issuer_lines.append(("Teléfono", settings.INVOICE_ISSUER_PHONE))
    if settings.INVOICE_ISSUER_EMAIL:
        issuer_lines.append(("Correo", settings.INVOICE_ISSUER_EMAIL))
    customer_lines = []
    if (
        data.get("nombre_recibe")
        and data["nombre_recibe"] != data["cliente_nombre"]
    ):
        customer_lines.append(("Recibe", data["nombre_recibe"]))
    for label, key in (
        ("Identificación", "identificacion"),
        ("Dirección", "direccion"),
        ("Teléfono", "telefono"),
        ("Correo", "cliente_email"),
    ):
        if data.get(key):
            customer_lines.append((label, data[key]))
    if not customer_lines:
        customer_lines = [("Correo", data.get("cliente_email", ""))]
    parties = Table(
        [[
            _party_block("DATOS DEL EMISOR", "Persianas & Cortinas Dany", issuer_lines, styles),
            _party_block("DATOS DEL CLIENTE", data["cliente_nombre"], customer_lines, styles),
        ]],
        colWidths=[CONTENT_WIDTH / 2, CONTENT_WIDTH / 2],
    )
    parties.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.extend([parties, Spacer(1, 5 * mm)])
    story.append(_product_table(data, styles))
    story.extend([Spacer(1, 2 * mm), _summary(data, styles), Spacer(1, 3 * mm)])

    method = data.get("metodo_pago") or "No informado"
    payment_status = data.get("estado_pago") or "Pendiente de confirmación"
    payment_text = (
        f"Método: {_escape(method)}<br/>"
        f"Estado: {_escape(payment_status)}<br/>"
        "Simulación académica; no se realizó un cobro real."
    )
    observations = _escape(data.get("observaciones") or "Sin observaciones registradas.")
    additional = (
        f"Estado del pedido: {_escape(data.get('estado_pedido', 'Registrado'))}<br/>"
        "Sin validación fiscal ni transmisión a la DIAN."
    )
    info_cards = Table(
        [[
            _info_card("Forma de pago", payment_text, "credit-card-outline-regular", styles, BEIGE),
            _info_card("Observaciones", observations, "edit-outline-regular", styles),
            _info_card("Información adicional", additional, "calendar-outline-regular", styles, BEIGE),
        ]],
        colWidths=[CONTENT_WIDTH / 3] * 3,
    )
    info_cards.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.extend([
        info_cards,
        Spacer(1, 3 * mm),
        _document_footer(invoice_number, cufe, issued_at, styles),
        Spacer(1, 2 * mm),
        Paragraph(
            "<b>Gracias por confiar en Persianas &amp; Cortinas Dany.</b> "
            "¡Hacemos de tus espacios, lugares únicos!",
            ParagraphStyle(
                "InvoiceThanks", parent=styles["body"], alignment=TA_CENTER,
                textColor=MUTED, fontSize=7.5, leading=10,
            ),
        ),
    ])
    document.build(story, onFirstPage=_page_decoration, onLaterPages=_page_decoration)
    return buffer.getvalue()


def _document_footer(invoice_number, cufe, issued_at, styles):
    qr_data = (
        f"DEMO-NO-FISCAL|pedido={invoice_number.removeprefix('DEMO-')}|"
        f"documento={invoice_number}|fecha={issued_at.isoformat()}"
    )
    contact_rows = [
        [
            _icon("map-pin", 3.5 * mm),
            Paragraph(
                _escape(settings.INVOICE_ISSUER_ADDRESS or "Datos de contacto de demostración"),
                styles["body"],
            ),
        ],
    ]
    if settings.INVOICE_ISSUER_PHONE:
        contact_rows.append([
            _icon("phone-call", 3.5 * mm),
            Paragraph(_escape(settings.INVOICE_ISSUER_PHONE), styles["body"]),
        ])
    if settings.INVOICE_ISSUER_EMAIL:
        contact_rows.append([
            _icon("mail-outline-regular", 3.5 * mm),
            Paragraph(_escape(settings.INVOICE_ISSUER_EMAIL), styles["body"]),
        ])
    contact_rows.append([
        Paragraph("<b>PERSIANAS &amp; CORTINAS DANY</b>", styles["body"]),
        "",
    ])
    contacts = Table(
        contact_rows,
        colWidths=[6 * mm, CONTENT_WIDTH / 3 - 10 * mm],
        style=TableStyle([
            ("SPAN", (-2, -1), (-1, -1)),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 1),
            ("TOPPADDING", (0, 0), (-1, -1), 1),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        ]),
    )
    social_icons = Table(
        [[
            _icon("brand-facebook", 5 * mm),
            _icon("brand-instagram", 5 * mm),
            _icon("brand-whatsapp", 5 * mm),
        ]],
        colWidths=[8 * mm, 8 * mm, 8 * mm],
        style=TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ]),
    )
    footer = Table(
        [[
            [DemoQrCode(qr_data), Paragraph("QR DEMOSTRACIÓN · NO FISCAL", styles["small"])],
            contacts,
            [
                Paragraph("IDENTIFICADOR / CUFE DEMO — NO FISCAL", styles["heading"]),
                Paragraph(_escape(cufe), styles["small"]),
                Spacer(1, 1.5 * mm),
                social_icons,
            ],
        ]],
        colWidths=[CONTENT_WIDTH / 3] * 3,
    )
    footer.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PALE),
        ("BOX", (0, 0), (-1, -1), 0.45, LINE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (0, 0), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return footer
