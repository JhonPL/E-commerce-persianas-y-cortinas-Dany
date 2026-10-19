from service_proxy import ServiceProxy


class CatalogServiceProxy(ServiceProxy):
    service_url_setting = "CATALOGO_SERVICE_URL"
    timeout_setting = "CATALOGO_SERVICE_TIMEOUT_SECONDS"
    service_label = "catálogo"
