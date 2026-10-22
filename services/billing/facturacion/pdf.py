from pathlib import Path
from urllib.parse import unquote, urlparse
from urllib.request import url2pathname

from django.template.loader import render_to_string


ASSET_DIR = Path(__file__).resolve().parent / "assets"


def _invoice_url_fetcher(url):
    from weasyprint import URLFetcher

    parsed_url = urlparse(url)
    fetcher = URLFetcher(
        allowed_protocols={"file", "data"},
        fail_on_errors=True,
    )
    if parsed_url.scheme == "data":
        return fetcher(url)
    if parsed_url.scheme != "file":
        raise ValueError("La factura solo puede cargar recursos locales.")

    resource_path = Path(url2pathname(unquote(parsed_url.path))).resolve()
    if not resource_path.is_relative_to(ASSET_DIR):
        raise ValueError("El recurso solicitado está fuera de los assets de factura.")
    return fetcher(url)


def render_invoice_document(context):
    from weasyprint import HTML

    html = render_to_string(
        "facturacion/invoice.html",
        context,
    )
    return HTML(
        string=html,
        base_url=ASSET_DIR.as_uri() + "/",
        url_fetcher=_invoice_url_fetcher,
    ).render()


def render_invoice_pdf(context):
    return render_invoice_document(context).write_pdf()
