from html import escape
from pathlib import Path
import smtplib
from email.mime.image import MIMEImage

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils.html import format_html


GREEN = "#268b35"
LIGHT_GREEN = "#eef5e6"
CREAM = "#f5f2e9"
DARK = "#10211b"
LOGO_CID = "brand-logo"


def _text(value):
    return escape(str(value or ""))


def _money(value):
    amount = f"{value:,.0f}".replace(",", ".")
    return f"${amount} COP"


def _button(label, url):
    return format_html(
        '<a href="{}" style="display:inline-block;padding:12px 25px;'
        'border-radius:24px;background:{};color:#fff;text-decoration:none;'
        'font-weight:bold;font-size:14px">{}</a>',
        url,
        GREEN,
        label,
    )


def _header():
    logo = (
        f'<img src="cid:{LOGO_CID}" width="62" height="62" alt="Persianas &amp; '
        'Cortinas Dany" style="display:block;width:62px;height:62px;'
        'border-radius:50%">'
    )
    return (
        '<tr><td style="padding:24px 26px;background:#fff">'
        '<table role="presentation" width="100%" cellspacing="0" cellpadding="0">'
        '<tr><td width="76" valign="middle">'
        f"{logo}"
        '</td><td valign="middle" style="padding-left:10px">'
        '<div style="font:700 14px Arial,sans-serif;letter-spacing:1px;'
        f'color:{DARK}">PERSIANAS &amp;<br>CORTINAS</div>'
        f'<div style="font:700 19px Arial,sans-serif;letter-spacing:2px;color:{GREEN}">'
        "DANY</div></td>"
        '<td align="right" style="font:12px Arial,sans-serif;color:#52615a">'
        "Diseño, elegancia y confort<br>para tus espacios"
        "</td></tr></table></td></tr>"
    )


def _footer():
    contact = _text(settings.CONTACT_EMAIL)
    return (
        f'<tr><td style="padding:18px 24px;background:{DARK};color:#fff">'
        '<table role="presentation" width="100%" cellspacing="0" cellpadding="0">'
        '<tr><td width="72" valign="middle">'
        f'<img src="cid:{LOGO_CID}" width="48" height="48" alt="" '
        'style="display:block;width:48px;height:48px;border-radius:50%">'
        '</td><td valign="middle" style="font:700 11px Arial,sans-serif;'
        'letter-spacing:1px">PERSIANAS &amp;<br>CORTINAS DANY</td>'
        '<td align="right" style="font:12px Arial,sans-serif">'
        '<span style="color:#cfe795">¿Necesitas ayuda?</span><br>'
        f'<a href="mailto:{contact}" style="color:#fff">{contact}</a>'
        "</td></tr></table></td></tr>"
    )


def _item_rows(items):
    rows = []
    for index, item in enumerate(items):
        background = "#ffffff" if index % 2 == 0 else "#f8faf5"
        rows.append(
            f'<tr style="background:{background}">'
            f'<td style="padding:10px 8px;border-bottom:1px solid #e7ece3;'
            f'font:13px Arial,sans-serif;color:{DARK}">'
            f'<strong>{_text(item["producto_nombre"])}</strong><br>'
            f'<span style="color:#64736b;font-size:11px">'
            f'{_text(item["ancho_cm"])} × {_text(item["alto_cm"])} cm</span></td>'
            '<td align="center" style="padding:10px 5px;border-bottom:1px solid #e7ece3;'
            'font:13px Arial,sans-serif">'
            f'{_text(item["cantidad"])}</td>'
            '<td align="right" style="padding:10px 8px;border-bottom:1px solid #e7ece3;'
            'font:13px Arial,sans-serif">'
            f'{_money(item["precio_total"])}</td></tr>'
        )
    return "".join(rows)


def _items_table(items, total):
    return (
        '<table role="presentation" width="100%" cellspacing="0" cellpadding="0" '
        'style="border:1px solid #e2e9dc;border-radius:10px;border-collapse:separate;'
        'border-spacing:0;overflow:hidden">'
        '<tr style="background:#f4f7ef">'
        '<th align="left" style="padding:10px 8px;font:700 11px Arial,sans-serif;'
        'color:#52615a">PRODUCTO</th>'
        '<th align="center" style="padding:10px 5px;font:700 11px Arial,sans-serif;'
        'color:#52615a">CANT.</th>'
        '<th align="right" style="padding:10px 8px;font:700 11px Arial,sans-serif;'
        'color:#52615a">TOTAL</th></tr>'
        f"{_item_rows(items)}"
        '<tr><td colspan="2" align="right" style="padding:12px 8px;'
        'font:700 14px Arial,sans-serif;color:#26372f">Total</td>'
        f'<td align="right" style="padding:12px 8px;font:700 16px Arial,sans-serif;'
        f'color:{GREEN}">{_money(total)}</td></tr></table>'
    )


def _progress(current_step):
    steps = ("Pedido confirmado", "En preparación", "En camino")
    cells = []
    for index, label in enumerate(steps):
        done = index <= current_step
        color = GREEN if done else "#bdc5bf"
        marker = "✓" if done else str(index + 1)
        cells.append(
            '<td align="center" width="33%" style="font:11px Arial,sans-serif;'
            'color:#52615a">'
            f'<span style="display:inline-block;width:26px;height:26px;line-height:26px;'
            f'border-radius:50%;background:{color};color:#fff;font-weight:bold">'
            f"{marker}</span><br><span style=\"display:inline-block;padding-top:6px\">"
            f"{_text(label)}</span></td>"
        )
    return (
        '<table role="presentation" width="100%" cellspacing="0" cellpadding="0" '
        'style="margin:16px 0 4px"><tr>'
        + "".join(cells)
        + "</tr></table>"
    )


def order_email_html(
    *,
    title,
    intro,
    order_id,
    total,
    items,
    cta_label,
    cta_url,
    status_label=None,
    recipient=None,
    address=None,
    notice=None,
    progress_step=None,
    extra_html="",
):
    details = [
        '<table role="presentation" width="100%" cellspacing="0" cellpadding="0" '
        f'style="margin:16px 0;background:#fff;border:1px solid #e6ecdf;'
        'border-radius:10px"><tr>'
        '<td style="padding:14px 16px;font:12px Arial,sans-serif;color:#64736b">'
        "NÚMERO DE PEDIDO<br>"
        f'<strong style="display:inline-block;padding-top:5px;font-size:14px;'
        f'color:{DARK}">#{_text(order_id)}</strong></td>'
    ]
    if status_label:
        details.append(
            '<td align="right" style="padding:14px 16px;font:12px Arial,sans-serif;'
            'color:#64736b">ESTADO DEL PEDIDO<br>'
            f'<strong style="display:inline-block;margin-top:5px;padding:6px 12px;'
            f'border-radius:14px;background:{LIGHT_GREEN};color:{GREEN}">'
            f"{_text(status_label)}</strong></td>"
        )
    details.append("</tr></table>")
    if progress_step is not None:
        details.append(_progress(progress_step))
    if recipient or address:
        details.append(
            '<table role="presentation" width="100%" cellspacing="0" cellpadding="0" '
            f'style="margin:14px 0;background:{LIGHT_GREEN};border-radius:10px"><tr>'
            '<td style="padding:14px 16px;font:12px Arial,sans-serif;line-height:1.6;'
            f'color:{DARK}"><strong>DATOS DE ENTREGA</strong><br>'
            f"{'<strong>Recibe:</strong> ' + _text(recipient) + '<br>' if recipient else ''}"
            f"{'<strong>Dirección:</strong> ' + _text(address) if address else ''}"
            "</td></tr></table>"
        )
    if items:
        details.append(_items_table(items, total))
    details.append(extra_html)
    if notice:
        details.append(
            f'<p style="margin:14px 0;padding:12px 14px;background:{CREAM};'
            'border-radius:8px;font:12px Arial,sans-serif;line-height:1.5;'
            f'color:#52615a">{_text(notice)}</p>'
        )
    details.append(
        f'<div style="padding:20px 0 6px;text-align:center">{_button(cta_label, cta_url)}</div>'
    )
    return (
        '<!doctype html><html lang="es"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1.0">'
        f"<title>{_text(title)}</title></head>"
        f'<body style="margin:0;padding:20px 8px;background:{CREAM};'
        'font-family:Arial,Helvetica,sans-serif">'
        '<div style="display:none;max-height:0;overflow:hidden">'
        f"{_text(intro)}</div>"
        '<table role="presentation" align="center" width="100%" cellspacing="0" '
        'cellpadding="0" style="max-width:680px;background:#fff;border-radius:12px;'
        'overflow:hidden">'
        f"{_header()}"
        f'<tr><td style="padding:0 24px 24px"><table role="presentation" width="100%" '
        f'cellspacing="0" cellpadding="0" style="background:{LIGHT_GREEN};'
        'border-radius:12px"><tr><td style="padding:22px">'
        f'<p style="margin:0 0 8px;font:700 20px Arial,sans-serif;color:{DARK}">'
        f"{_text(title)}</p>"
        f'<p style="margin:0;font:14px Arial,sans-serif;line-height:1.6;color:#45564d">'
        f"{_text(intro)}</p></td></tr></table>"
        f'{"".join(details)}</td></tr>'
        f"{_footer()}"
        "</table></body></html>"
    )


def send_order_email(
    *,
    subject,
    body,
    html_body,
    recipient,
    reply_to=None,
    attachments=(),
):
    email = EmailMultiAlternatives(
        subject,
        body,
        settings.DEFAULT_FROM_EMAIL,
        [recipient],
        reply_to=[reply_to] if reply_to else None,
    )
    email.attach_alternative(html_body, "text/html")
    for filename, content, mimetype in attachments:
        email.attach(filename, content, mimetype)
    logo_path = (
        Path(__file__).resolve().parent / "assets" / "logogreen.png"
    )
    with logo_path.open("rb") as logo_file:
        logo = MIMEImage(logo_file.read(), _subtype="png")
    logo.add_header("Content-ID", f"<{LOGO_CID}>")
    logo.add_header("Content-Disposition", "inline", filename="logogreen.png")
    email.attach(logo)
    sent_count = email.send(fail_silently=False)
    if sent_count != 1:
        raise smtplib.SMTPException("El servidor de correo no confirmó el envío.")
