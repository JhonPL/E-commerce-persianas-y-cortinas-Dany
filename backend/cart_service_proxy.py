from service_proxy import ServiceProxy


class CartServiceProxy(ServiceProxy):
    service_url_setting = "CART_SERVICE_URL"
    timeout_setting = "CART_SERVICE_TIMEOUT_SECONDS"
    service_label = "carrito"
