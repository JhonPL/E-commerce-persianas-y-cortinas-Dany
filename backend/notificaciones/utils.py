from django.core.mail import send_mail
from django.conf import settings
from .models import NotificacionAdmin


def notificar_admin(pedido):
    destinatario = getattr(settings, 'ADMIN_EMAIL', 'admin@tutienda.com')
    try:
        send_mail(
            subject = f'🛒 Nuevo pedido #{pedido.pedido_id} — ${pedido.total:,.0f} COP',
            message = (
                f'Se realizó un nuevo pedido.\n\n'
                f'Pedido ID: {pedido.pedido_id}\n'
                f'Cliente: {pedido.cliente.usuario.email}\n'
                f'Total: ${pedido.total:,.0f} COP\n'
            ),
            from_email    = settings.DEFAULT_FROM_EMAIL,
            recipient_list = [destinatario],
            fail_silently = False,
        )
        NotificacionAdmin.objects.create(
            pedido       = pedido,
            destinatario = destinatario,
            estado       = NotificacionAdmin.ENVIADO,
        )
    except Exception as e:
        NotificacionAdmin.objects.create(
            pedido        = pedido,
            destinatario  = destinatario,
            estado        = NotificacionAdmin.FALLIDO,
            error_detalle = str(e),
        )