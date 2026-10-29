from unittest.mock import patch

from django.test import SimpleTestCase, override_settings
from rest_framework.test import APIClient


class ExpirationSchedulerEndpointTests(SimpleTestCase):
    url = "/api/internal/pedidos/expire-unpaid-orders/"

    @override_settings(EXPIRATION_JOB_TOKEN="scheduler-test-token")
    def test_rejects_requests_without_the_scheduler_token(self):
        response = APIClient().post(self.url)

        self.assertEqual(response.status_code, 401)

    @override_settings(EXPIRATION_JOB_TOKEN="scheduler-test-token")
    def test_rejects_an_invalid_scheduler_token(self):
        response = APIClient().post(
            self.url,
            HTTP_X_EXPIRATION_JOB_TOKEN="wrong-token",
        )

        self.assertEqual(response.status_code, 401)

    @override_settings(EXPIRATION_JOB_TOKEN="scheduler-test-token")
    @patch("pedidos.views._expire_due_unpaid_orders", return_value=2)
    def test_expires_due_orders_with_the_dedicated_token(self, expire_orders):
        response = APIClient().post(
            self.url,
            HTTP_X_EXPIRATION_JOB_TOKEN="scheduler-test-token",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"rejected": 2})
        expire_orders.assert_called_once_with()

    @override_settings(EXPIRATION_JOB_TOKEN="")
    def test_reports_missing_scheduler_configuration(self):
        response = APIClient().post(
            self.url,
            HTTP_X_EXPIRATION_JOB_TOKEN="scheduler-test-token",
        )

        self.assertEqual(response.status_code, 503)
