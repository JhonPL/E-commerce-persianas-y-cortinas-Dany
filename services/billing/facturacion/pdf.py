from decimal import Decimal
from html import escape
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


GREEN = colors.HexColor("#58a52d")
LIGHT_GREEN = colors.HexColor("#edf5e5")
CREAM = colors.HexColor("#f8f7f1")
DARK = colors.HexColor("#17221a")
MUTED = colors.HexColor("#5e695f")


def _money(value):
    amount = f"{Decimal(value):,.0f}".replace(",", ".")
    return f"$ {amount} COP"


def _paragraph_styles():
    base = getSampleStyleSheet()
    return {
        "brand": ParagraphStyle(
            "InvoiceBrand",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=15,
            leading=18,
            textColor=DARK,
        ),
        "title": ParagraphStyle(
            "InvoiceTitle",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            alignment=TA_RIGHT,
            textColor=DARK,
        ),
        "heading": ParagraphStyle(
            "InvoiceHeading",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=12,
            textColor=GREEN,
        ),
        "body": ParagraphStyle(
            "InvoiceBody",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=12,
            textColor=DARK,
        ),
        "small": ParagraphStyle(
            "InvoiceSmall",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=7.5,
            leading=10,
            textColor=MUTED,
        ),
        "total": ParagraphStyle(
            "InvoiceTotal",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=16,
            textColor=DARK,
        ),
    }


def build_demo_invoice_pdf(*, invoice_number, issued_at, data):
    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=13 * mm,
        bottomMargin=14 * mm,
        pageCompression=0,
        title=f"Comprobante de demostración {invoice_number}",
        author="Persianas & Cortinas Dany",
    )
    styles = _paragraph_styles()
    paragraph = lambda text, style="body": Paragraph(text, styles[style])
    story = []

    brand = Table(
        [[
            paragraph("<b>P&amp;D</b>", "heading"),
            [
                paragraph("PERSIANAS &amp; CORTINAS", "brand"),
                paragraph("DANY  |  Diseño, elegancia y confort", "small"),
            ],
            [
                paragraph("COMPROBANTE DE PAGO", "title"),
                paragraph(
                    f"<b>{escape(invoice_number)}</b><br/>"
                    f"Fecha de emisión: {issued_at.strftime('%d/%m/%Y %H:%M')}",
                    "body",
                ),
            ],
        ]],
        colWidths=[18 * mm, 78 * mm, 85 * mm],
    )
    brand.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), GREEN),
        ("TEXTCOLOR", (0, 0), (0, 0), colors.white),
        ("ALIGN", (0, 0), (0, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 11),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 11),
        ("LINEBELOW", (0, 0), (-1, -1), 1.2, GREEN),
    ]))
    story.extend([brand, Spacer(1, 7 * mm)])

    issuer = (
        paragraph("DATOS DEL EMISOR", "heading"),
        paragraph("Persianas &amp; Cortinas Dany<br/>"
                  "Documento generado para demostración académica", "body"),
    )
    customer = (
        paragraph("DATOS DEL CLIENTE", "heading"),
        paragraph(
            f"{escape(data['cliente_nombre'])}<br/>{escape(data['cliente_email'])}<br/>"
            f"{escape(data.get('direccion', ''))}",
            "body",
        ),
    )
    parties = Table([[list(issuer), list(customer)]], colWidths=[90 * mm, 91 * mm])
    parties.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), CREAM),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5eadf")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.white),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
    ]))
    story.extend([parties, Spacer(1, 7 * mm)])

    rows = [["DESCRIPCION", "CANT.", "TOTAL"]]
    for item in data["detalles"]:
        dimensions = f"{item['ancho_cm']} x {item['alto_cm']} cm"
        rows.append([
            paragraph(
                f"<b>{escape(item['producto_nombre'])}</b><br/>"
                f"<font color='#5e695f'>{escape(dimensions)}</font>"
            ),
            paragraph(str(item["cantidad"])),
            paragraph(_money(item["precio_total"])),
        ])
    items = Table(rows, colWidths=[112 * mm, 25 * mm, 44 * mm], repeatRows=1)
    items.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), GREEN),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dce5d4")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, CREAM]),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
    ]))
    story.extend([items, Spacer(1, 4 * mm)])

    summary = Table(
        [[paragraph("TOTAL DEL PEDIDO", "total"), paragraph(_money(data["total"]), "total")]],
        colWidths=[120 * mm, 61 * mm],
    )
    summary.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_GREEN),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
    ]))
    story.extend([summary, Spacer(1, 7 * mm)])

    disclaimer = Table(
        [[paragraph(
            "<b>PAGO SIMULADO - SIN COBRO REAL</b><br/>"
            "Este documento es una demostracion academica. No es una factura "
            "electronica validada por la DIAN, no tiene CUFE y no acredita un pago real.",
            "body",
        )]],
        colWidths=[181 * mm],
    )
    disclaimer.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), CREAM),
        ("BOX", (0, 0), (-1, -1), 0.8, GREEN),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(disclaimer)
    document.build(story)
    return buffer.getvalue()