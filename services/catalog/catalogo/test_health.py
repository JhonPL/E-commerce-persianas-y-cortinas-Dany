from unittest.mock import patch

from django.db import OperationalError
from django.test import TestCase


class HealthEndpointTests(TestCase):
    def test_live_and_ready_endpoints(self):
        for path in ("/health/live/", "/health/ready/"):
            with self.subTest(path=path):
                response = self.client.get(path)

                self.assertEqual(response.status_code, 200)
                self.assertEqual(
                    response.json(),
                    {"status": "ok", "service": "catalog"},
                )

    def test_ready_returns_503_when_database_is_unavailable(self):
        with patch(
            "catalogo.health.connection.cursor",
            side_effect=OperationalError("database unavailable"),
        ):
            response = self.client.get("/health/ready/")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json(),
            {"status": "not_ready", "service": "catalog"},
        )
