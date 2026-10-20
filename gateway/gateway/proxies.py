import requests
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt


@method_decorator(csrf_exempt, name="dispatch")
class ServiceProxy(View):
    service_url_setting = ""
    service_label = ""
    timeout_setting = "SERVICE_TIMEOUT_SECONDS"

    def dispatch(self, request, *args, **kwargs):
        prefixes = kwargs.pop("prefixes", ())
        subpath = kwargs.get("subpath", "")
        path_parts = (*prefixes, subpath)
        relative_path = "/".join(
            part.strip("/")
            for part in path_parts
            if part and part.strip("/")
        )
        endpoint = getattr(settings, self.service_url_setting).rstrip("/")
        endpoint += f"/{relative_path}/" if relative_path else "/"

        headers = {
            key: value
            for key, value in (
                ("Authorization", request.headers.get("Authorization")),
                ("Content-Type", request.headers.get("Content-Type")),
                ("Accept", request.headers.get("Accept")),
            )
            if value
        }
        params = [
            (key, value)
            for key in request.GET
            for value in request.GET.getlist(key)
        ]
        try:
            upstream = requests.request(
                request.method,
                endpoint,
                params=params,
                data=request.body if request.method not in ("GET", "HEAD") else None,
                headers=headers,
                timeout=getattr(settings, self.timeout_setting),
                allow_redirects=False,
            )
        except requests.RequestException:
            return JsonResponse(
                {"detail": f"El servicio de {self.service_label} no está disponible."},
                status=503,
            )

        response = HttpResponse(
            upstream.content,
            status=upstream.status_code,
            content_type=upstream.headers.get("Content-Type"),
        )
        for header in ("Content-Disposition", "Allow", "Location"):
            if value := upstream.headers.get(header):
                response[header] = value
        return response


class IdentityServiceProxy(ServiceProxy):
    service_url_setting = "IDENTITY_SERVICE_URL"
    service_label = "identidad"


class CatalogServiceProxy(ServiceProxy):
    service_url_setting = "CATALOGO_SERVICE_URL"
    service_label = "catálogo"


class CartServiceProxy(ServiceProxy):
    service_url_setting = "CART_SERVICE_URL"
    service_label = "carrito"


class OrdersServiceProxy(ServiceProxy):
    service_url_setting = "ORDERS_SERVICE_URL"
    service_label = "pedidos"
    timeout_setting = "ORDERS_SERVICE_TIMEOUT_SECONDS"


class PaymentsServiceProxy(ServiceProxy):
    service_url_setting = "PAYMENTS_SERVICE_URL"
    service_label = "simulación de pagos"
