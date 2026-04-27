import uuid
from django.conf import settings
from django.urls import reverse
from django.core.exceptions import ImproperlyConfigured

if settings.USE_YOOKASSA:
    from yookassa import Configuration, Payment
else:
    # Define dummy classes if yookassa is not used
    class Configuration:
        account_id = None
        secret_key = None

    class Payment:
        @staticmethod
        def create(data):
            raise ImproperlyConfigured("YooKassa is not configured. Payment cannot be created.")


def create_yookassa_payment(request, order_id, total_cost):
    """
    Creates a YooKassa payment object.
    """
    if not settings.USE_YOOKASSA:
        # If yookassa is not enabled, raise an exception or handle it with a dummy payment.
        # For now, let's raise an exception to clearly indicate the misconfiguration.
        raise ImproperlyConfigured(
            "YooKassa payment is not enabled. Please configure YOOKASSA_SHOP_ID and YOOKASSA_SECRET_KEY in settings.py "
            "or ensure settings.USE_YOOKASSA is True if you intend to use it."
        )

    Configuration.account_id = settings.YOOKASSA_SHOP_ID
    Configuration.secret_key = settings.YOOKASSA_SECRET_KEY

    idempotence_key = str(uuid.uuid4())

    return_url = request.build_absolute_uri(reverse('app:payment_done'))

    payment = Payment.create({
        "amount": {
            "value": f"{total_cost:.2f}",
            "currency": "RUB"
        },
        "confirmation": {
            "type": "redirect",
            "return_url": return_url 
        },
        "capture": True,
        "description": f"Заказ №{order_id}",
        "metadata": {
            "order_id": str(order_id)
        }
    }, idempotence_key)

    return payment
