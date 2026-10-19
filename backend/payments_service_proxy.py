from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from service_proxy import ServiceProxy


@method_decorator(csrf_exempt, name="dispatch")
class PaymentsServiceProxy(ServiceProxy):
    service_url_setting = "PAYMENTS_SERVICE_URL"
    timeout_setting = "PAYMENTS_SERVICE_TIMEOUT_SECONDS"
    service_label = "pagos simulado"
