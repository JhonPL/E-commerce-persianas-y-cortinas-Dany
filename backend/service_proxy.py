import requests
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt


@method_decorator(csrf_exempt, name="dispatch")
class ServiceProxy(View):
    service_url_setting = ""
    timeout_setting = ""
    service_label = ""

    forwarded_request_headers = {
        "HTTP_AUTHORIZATION": "Authorization",
        "CONTENT_TYPE": "Content-Type",
        "HTTP_ACCEPT": "Accept",
    }
    forwarded_response_headers = ("Content-Disposition", "Allow", "Location")

    def dispatch(self, request, *args, **kwargs):
        subpath = kwargs.get("subpath", "")
        endpoint = getattr(settings, self.service_url_setting).rstrip("/")
        if subpath:
            endpoint += f"/{subpath.strip('/')}/"
        else:
            endpoint += "/"

        headers = {
            header_name: value
            for key, header_name in self.forwarded_request_headers.items()
            if (value := request.META.get(key))
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
                {
                    "detail": (
                        f"El servicio de {self.service_label} no está disponible."
                    )
                },
                status=503,
            )

        response = HttpResponse(
            upstream.content,
            status=upstream.status_code,
            content_type=upstream.headers.get("Content-Type"),
        )
        for header in self.forwarded_response_headers:
            value = upstream.headers.get(header)
            if value:
                response[header] = value
        return response
