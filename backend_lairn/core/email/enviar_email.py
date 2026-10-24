"""
Envío de correos transaccionales (por ahora, solo recuperación de contraseña).

Usa Resend (ya estaba en requirements.txt, sin usar en ningún lado) si hay
una `RESEND_API_KEY` configurada — pensado para producción, sin necesidad de
levantar un servidor SMTP propio. Si no hay key (el caso normal en
desarrollo local, donde nadie tiene una cuenta de Resend a mano), cae al
`EMAIL_BACKEND` de Django configurado en settings.py, que por defecto es el
backend de consola: el correo se imprime en los logs del contenedor en vez
de enviarse de verdad, así que todo el flujo se puede probar de punta a
punta sin depender de un servicio externo ni gastar cuota de nada.
"""

import logging

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def enviar_email(destinatario: str, asunto: str, cuerpo_html: str, cuerpo_texto: str) -> None:
    if settings.RESEND_API_KEY:
        import resend

        resend.api_key = settings.RESEND_API_KEY
        resend.Emails.send({
            'from': settings.DEFAULT_FROM_EMAIL,
            'to': [destinatario],
            'subject': asunto,
            'html': cuerpo_html,
        })
        return

    send_mail(
        subject=asunto,
        message=cuerpo_texto,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[destinatario],
        html_message=cuerpo_html,
    )
