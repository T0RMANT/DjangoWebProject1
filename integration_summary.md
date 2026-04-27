# DjangoWebProject1/app/payment.py
```python
import uuid
from yookassa import Configuration, Payment
from django.conf import settings
from django.urls import reverse

def create_yookassa_payment(request, order_id, total_cost):
    """
    Creates a YooKassa payment object.
    """
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
```

# DjangoWebProject1/app/views.py (within `payment_process` function)
```python
@login_required
def payment_process(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    total_cost = order.get_total_cost()

    if total_cost == 0:
        order.paid = True
        order.save()
        return redirect('app:payment_done')

    payment = create_yookassa_payment(request, order.id, total_cost)
    order.yookassa_payment_id = payment.id
    order.save()

    return redirect(payment.confirmation.confirmation_url)
```

# DjangoWebProject1/app/templates/app/checkout.html (within payment methods section)
```html
                <p><strong>Картой онлайн (ЮKassa)</strong></p>
                <div class="well" style="background-color: #eee;">
                    <p class="text-center" style="padding-top: 20px;">После размещения заказа вы будете перенаправлены на страницу оплаты ЮKassa.</p>
                </div>
```