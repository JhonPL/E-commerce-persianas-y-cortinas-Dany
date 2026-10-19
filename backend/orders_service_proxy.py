from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from service_proxy import ServiceProxy


@method_decorator(csrf_exempt, name="dispatch")
class OrdersServiceProxy(ServiceProxy):
    service_url_setting = "ORDERS_SERVICE_URL"
    timeout_setting = "ORDERS_SERVICE_TIMEOUT_SECONDS"
    service_label = "pedidos"

    def dispatch(self, request, *args, **kwargs):
        prefixes = kwargs.pop("prefixes", ())
        subpath = kwargs.get("subpath", "")
        kwargs["subpath"] = "/".join(
            part.strip("/")
            for part in (*prefixes, subpath)
            if part and part.strip("/")
        )
        return super().dispatch(request, *args, **kwargs)
