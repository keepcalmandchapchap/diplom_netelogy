from django.core.mail import send_mail, EmailMessage
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from weasyprint import HTML
import tempfile

from django.contrib.auth import get_user_model
from django.core.signing import dumps
from django.core.signing import BadSignature, SignatureExpired, loads

User = get_user_model()

def generate_activation_token(user):
    return dumps(user.pk)

def validate_activation_token(token):
    from django.core.signing import BadSignature, SignatureExpired, loads
    try:
        user_id = loads(token, max_age=86400)
        user = User.objects.get(pk=user_id)
        return user
    except (BadSignature, SignatureExpired):
        return None
    except User.DoesNotExist:
        return None


def send_customer_order_confirmation(order):
        """Письмо клиенту о создании заказа"""
        subject = f'Ваш заказ #{order.id} успешно оформлен!'
        html_message = render_to_string('emails/order_confirmation.html', {'order': order})
        plain_message = strip_tags(html_message)
        from_email = settings.DEFAULT_FROM_EMAIL
        to_email = [order.user.email]

        send_mail(
            subject,
            plain_message,
            from_email,
            to_email,
            html_message=html_message,
            fail_silently=False
        )


def send_order_delivered_email(order):
    """
    Отправляет клиенту письмо о том, что заказ успешно доставлен
    """
    subject = f'Ваш заказ #{order.id} успешно доставлен!'
    html_message = render_to_string('emails/order_delivered.html', {'order': order})
    plain_message = strip_tags(html_message)
    from_email = settings.DEFAULT_FROM_EMAIL
    to_email = [order.user.email]

    send_mail(
        subject,
        plain_message,
        from_email,
        to_email,
        html_message=html_message,
        fail_silently=False
        )


def generate_and_send_invoice_pdf(order):
        """Генерация PDF и отправка на рабочую почту"""
        html_string = render_to_string('emails/invoice_template.html', {'order': order})
        html = HTML(string=html_string)
        pdf = html.write_pdf()

        subject = f'Новый заказ #{order.id} — накладная'
        from_email = settings.DEFAULT_FROM_EMAIL
        to_email = [settings.ORDER_NOTIFICATION_EMAIL]

        email = EmailMessage(
            subject,
            'Во вложении накладная по заказу.',
            from_email,
            to_email
        )
        # Добавляем PDF как вложение
        email.attach(f'order_{order.id}.pdf', pdf, 'application/pdf')
        email.send(fail_silently=False)