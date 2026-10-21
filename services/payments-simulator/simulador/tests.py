from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import Mock, patch
import uuid

from django.test import override_settings
from rest_framework.test import APIRequestFactory, APITestCase, force_authenticate

from .models import PaymentAttempt
from .views import SimulatePaymentView


@override_settings(
    INTERNAL_SERVICE_TOKEN="test-internal-token",
    PAYMENT_SIMULATOR_ENABLED=True,
    ORDERS_SERVICE_URL="http://orders.test",
    ORDERS_SERVICE_TIMEOUT_SECONDS=45,
)
class PaymentSimulationTests(APITestCase):
    def setUp(self):
        self.user = SimpleNamespace(
            usuario_id=17,
            is_authenticated=True,
            is_anonymous=False,
        )
        self.factory = APIRequestFactory()
        self.view = SimulatePaymentView.as_view()
        self.request_id = str(uuid.uuid4())

    @patch("simulador.views.requests.request")
    def test_simulates_approval_and_updates_the_order(self, request):
        context = Mock(
            status_code=200,
            json=lambda: {
                "pedido_id": 31,
                "usuario_id": 17,
                "total": "119000.00",
                "estado": "Pendiente de pago",
            },
        )
        result = Mock(
            status_code=200,
            json=lambda: {
                "estado": "Pendiente de preparación",
                "notificacion": "enviado",
            },
        )
        request.side_effect = [context, result]
        api_request = self.factory.post(
            "/api/v1/payments/simulate/",
            {
                "pedido_id": 31,
                "outcome": "approved",
                "request_id": self.request_id,
            },
            format="json",
        )
        force_authenticate(api_request, user=self.user)

        response = self.view(api_request)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["simulated"])
        self.assertEqual(response.data["outcome"], "approved")
        self.assertEqual(response.data["amount"], "119000.00")
        self.assertEqual(response.data["notification"], "enviado")
        self.assertEqual(request.call_count, 2)
        self.assertTrue(
            all(call.kwargs["timeout"] == 45 for call in request.call_args_list)
        )
        self.assertEqual(PaymentAttempt.objects.count(), 1)
        self.assertEqual(
            request.call_args_list[1].kwargs["json"]["amount"],
            "119000.00",
        )
        self.assertEqual(
            set(request.call_args_list[1].kwargs["json"]),
            {"outcome", "payment_reference", "amount"},
        )

    @patch("simulador.views.requests.request")
    def test_customer_cannot_simulate_payment_for_another_users_order(self, request):
        request.return_value = Mock(
            status_code=200,
            json=lambda: {
                "pedido_id": 31,
                "usuario_id": 99,
                "total": "119000.00",
                "estado": "Pendiente de pago",
            },
        )
        api_request = self.factory.post(
            "/api/v1/payments/simulate/",
            {
                "pedido_id": 31,
                "outcome": "approved",
                "request_id": self.request_id,
            },
            format="json",
        )
        force_authenticate(api_request, user=self.user)

        response = self.view(api_request)

        self.assertEqual(response.status_code, 404)
        request.assert_called_once()
        self.assertFalse(PaymentAttempt.objects.exists())

    @override_settings(PAYMENT_SIMULATOR_ENABLED=False)
    @patch("simulador.views.requests.request")
    def test_simulator_is_unavailable_when_disabled(self, request):
        api_request = self.factory.post(
            "/api/v1/payments/simulate/",
            {
                "pedido_id": 31,
                "outcome": "approved",
                "request_id": self.request_id,
            },
            format="json",
        )
        force_authenticate(api_request, user=self.user)

        response = self.view(api_request)

        self.assertEqual(response.status_code, 503)
        request.assert_not_called()

    @patch("simulador.views.requests.request")
    def test_reusing_idempotency_key_with_changed_outcome_is_rejected(self, request):
        request.return_value = Mock(
            status_code=200,
            json=lambda: {
                "pedido_id": 31,
                "usuario_id": 17,
                "total": "119000.00",
                "estado": "Pendiente de pago",
            },
        )
        PaymentAttempt.objects.create(
            pedido_id=31,
            request_id=self.request_id,
            usuario_id=17,
            amount=Decimal("119000.00"),
            outcome=PaymentAttempt.Outcome.APPROVED,
        )
        api_request = self.factory.post(
            "/api/v1/payments/simulate/",
            {
                "pedido_id": 31,
                "outcome": "declined",
                "request_id": self.request_id,
            },
            format="json",
        )
        force_authenticate(api_request, user=self.user)

        response = self.view(api_request)

        self.assertEqual(response.status_code, 409)
        request.assert_not_called()

    @patch("simulador.views.requests.request")
    def test_replaying_the_same_approved_request_reconciles_the_order(self, request):
        PaymentAttempt.objects.create(
            pedido_id=31,
            request_id=self.request_id,
            usuario_id=17,
            amount=Decimal("119000.00"),
            outcome=PaymentAttempt.Outcome.APPROVED,
        )
        request.return_value = Mock(
            status_code=200,
            json=lambda: {"pedido_id": 31, "duplicate": True},
        )
        api_request = self.factory.post(
            "/api/v1/payments/simulate/",
            {
                "pedido_id": 31,
                "outcome": "approved",
                "request_id": self.request_id,
            },
            format="json",
        )
        force_authenticate(api_request, user=self.user)

        response = self.view(api_request)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["duplicate"])
        request.assert_called_once()
        self.assertIn("payment-result", request.call_args.args[1])