import hmac, hashlib, json
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Pago, MetodoPago
from pedidos.models import Pedido, EstadoPedido, HistorialEstadoPedido
from notificaciones.utils import notificar_admin


class IniciarPagoView(APIView):
    """Devuelve los datos necesarios para iniciar el widget de Wompi"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        pedido_id = request.data.get('pedido_id')
        pedido    = generics.get_object_or_404(
            Pedido, pk=pedido_id, cliente=request.user.cliente
        )
        return Response({
            'public_key':  settings.WOMPI_PUBLIC_KEY,
            'monto_en_centavos': int(pedido.total * 100),
            'referencia':  f'PEDIDO-{pedido.pedido_id}',
            'moneda':      'COP',
        })


class WompiWebhookView(APIView):
    """Recibe confirmación de Wompi — NO requiere autenticación"""
    permission_classes = [AllowAny]

    def post(self, request):
        # 1. Verificar firma del evento
        checksum = request.headers.get('X-Event-Checksum', '')
        body     = json.dumps(request.data, separators=(',', ':'))
        firma    = hmac.new(
            settings.WOMPI_EVENT_KEY.encode(),
            body.encode(),
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(firma, checksum):
            return Response({'error': 'Firma inválida'}, status=401)

        # 2. Procesar la transacción
        datos        = request.data.get('data', {}).get('transaction', {})
        referencia   = datos.get('reference', '')
        estado_wompi = datos.get('status', '')
        tx_id        = datos.get('id', '')

        try:
            pedido_id = int(referencia.replace('PEDIDO-', ''))
            pedido    = Pedido.objects.get(pk=pedido_id)
        except (Pedido.DoesNotExist, ValueError):
            return Response({'error': 'Pedido no encontrado'}, status=404)

        # 3. Crear o actualizar pago
        metodo, _ = MetodoPago.objects.get_or_create(nombre='Tarjeta crédito')
        pago, _   = Pago.objects.get_or_create(
            referencia_pasarela = tx_id,
            defaults = {
                'pedido': pedido,
                'metodo': metodo,
                'monto':  pedido.total,
            }
        )
        pago.estado_pago = 'aprobado' if estado_wompi == 'APPROVED' else 'rechazado'
        pago.save()

        # 4. Si aprobado → cambiar estado del pedido + notificar admin
        if pago.estado_pago == 'aprobado':
            estado_pendiente = EstadoPedido.objects.get(
                nombre='Pendiente de preparación'
            )
            pedido.estado = estado_pendiente
            pedido.save()
            notificar_admin(pedido)

        return Response({'status': 'ok'})