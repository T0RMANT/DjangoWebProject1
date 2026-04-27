from datetime import datetime
import json
import logging

from django.conf import settings
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Avg, Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import slugify
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.core.mail import send_mail
from django.contrib.auth import login
from django.core.exceptions import ImproperlyConfigured

if settings.USE_YOOKASSA:
    from yookassa import Payment, Webhook
else:
    class Payment:
        # Dummy Payment class if yookassa is not used
        # You might need to add methods here that are called in your code
        # For now, a simple placeholder that raises an error if used
        def __init__(self, *args, **kwargs):
            raise ImproperlyConfigured("YooKassa Payment is not enabled.")

    class Webhook:
        # Dummy Webhook class if yookassa is not used
        # You might need to add methods here that are called in your code
        # For now, a simple placeholder that raises an error if used
        def __init__(self, *args, **kwargs):
            raise ImproperlyConfigured("YooKassa Webhook is not enabled.")
        
        @staticmethod
        def get_notification(request_body):
            raise ImproperlyConfigured("YooKassa Webhook is not enabled.")


from .cart import Cart
from .forms import (CartAddProductForm, CustomUserCreationForm,
                    OrderCreateForm, ReviewForm, PostForm, CommentForm)
from .models import (Category, Order, OrderItem, Product, Review, Post, Comment)
from .payment import create_yookassa_payment


def product_list(request, category_slug=None):
    """Renders the product list page, optionally filtered by category."""
    category = None
    categories = Category.objects.all()
    products = Product.objects.filter(available=True).annotate(avg_rating=Avg('reviews__rating'))
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)

    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)

    sort = request.GET.get('sort')
    if sort in ['name', 'price', '-price']:
        products = products.order_by(sort)

    return render(
        request,
        'app/index.html',  # Using index.html as the main catalog page for now
        {
            'title': 'Каталог товаров',
            'year': datetime.now().year,
            'category': category,
            'categories': categories,
            'products': products
        }
    )

def product_detail(request, id, slug):
    """Renders the product detail page and handles review submission."""
    product = get_object_or_404(Product, id=id, slug=slug, available=True)
    product_images = product.images.all()
    reviews = product.reviews.all()
    new_review = None
    can_review = False
    user_review = None

    if request.user.is_authenticated:
        user_review = reviews.filter(author=request.user).first()
        if Order.objects.filter(user=request.user, status='completed', items__product=product).exists() and not user_review:
            can_review = True

    if request.method == 'POST':
        if not can_review:
            return redirect(product.get_absolute_url())

        review_form = ReviewForm(data=request.POST)
        if review_form.is_valid():
            new_review = review_form.save(commit=False)
            new_review.product = product
            new_review.author = request.user
            new_review.save()
            return redirect(product.get_absolute_url())
        else:
            logging.error("Review form is not valid. Errors: %s", review_form.errors)
    else:
        review_form = ReviewForm()

    cart_product_form = CartAddProductForm()
    return render(
        request,
        'app/product_detail.html',
        {
            'title': product.name,
            'year': datetime.now().year,
            'product': product,
            'product_images': product_images,
            'reviews': reviews,
            'new_review': new_review,
            'review_form': review_form,
            'cart_product_form': cart_product_form,
            'can_review': can_review,
            'user_review': user_review,
        }
    )

@login_required
def delete_review(request, review_id):
    review = get_object_or_404(Review, id=review_id)
    if request.user == review.author:
        product = review.product
        review.delete()
        return redirect(product.get_absolute_url())
    else:
        # In a real app, you might want to return a 403 Forbidden response.
        return redirect('app:product_list')


def contact(request):
    """Renders the contact page."""
    assert isinstance(request, HttpRequest)
    return render(
        request,
        'app/contact.html',
        {
            'title': 'Контакты',
            'year': datetime.now().year,
        }
    )

def about(request):
    """Renders the about page."""
    assert isinstance(request, HttpRequest)
    return render(
        request,
        'app/about.html',
        {
            'title': 'Информация',
            'message': 'Сайт для продажи мерча.',
            'year': datetime.now().year,
        }
    )

def registration(request: HttpRequest):
    """Renders the registration page."""
    assert isinstance(request, HttpRequest)

    if request.method == "POST":
        regform = CustomUserCreationForm(request.POST)
        if regform.is_valid():
            reg_f = regform.save(commit=False)
            reg_f.is_staff = False
            reg_f.is_active = True
            reg_f.is_superuser = False
            reg_f.date_joined = datetime.now()
            reg_f.last_login = datetime.now()
            reg_f.save()
            login(request, reg_f)
            return redirect('app:product_list') # Redirect to the product list after registration
    else:
        regform = CustomUserCreationForm()

    return render(
        request,
        'app/registration.html',
        {
            'regform': regform,
            'year': datetime.now().year,
        }
    )
def delivery(request):
    """Renders the delivery and payment page."""
    assert isinstance(request, HttpRequest)
    return render(
        request,
        'app/delivery.html',
        {
            'title': 'Доставка и оплата',
            'year': datetime.now().year,
        }
    )

@require_POST
def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    form = CartAddProductForm(request.POST)
    if form.is_valid():
        cd = form.cleaned_data
        cart.add(product=product,
                 quantity=cd['quantity'],
                 update_quantity=cd['update'])
    return redirect('app:cart_detail')

def cart_remove(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    return redirect('app:cart_detail')

def cart_detail(request):
    cart = Cart(request)
    for item in cart:
        item['update_quantity_form'] = CartAddProductForm(initial={'quantity': item['quantity'],
                                                                    'update': True})
    return render(request, 'app/cart.html', {'cart': cart, 'title': 'Корзина'})

@login_required
def order_create(request):
    cart = Cart(request)
    if request.method == 'POST':
        post_data = request.POST.copy()
        # Since the user is always authenticated, we can safely get the email from the user object
        post_data['email'] = request.user.email
        form = OrderCreateForm(post_data)

        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user
            order.save()
            for item in cart:
                OrderItem.objects.create(order=order,
                                         product=item['product'],
                                         price=item['price'],
                                         quantity=item['quantity'])
            # clear the cart
            cart.clear()
            # Launch payment process
            return redirect('app:dummy_payment', order_id=order.id)
    else:
        initial_data = {
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'email': request.user.email
        }
        form = OrderCreateForm(initial=initial_data)
    return render(request,
                  'app/checkout.html',
                  {'cart': cart, 'form': form})

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

@login_required
def dummy_payment(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if request.method == 'POST':
        # "Pay" the order
        order.paid = True
        order.status = 'processing'
        order.save()

        # Send email
        send_mail(
            'Заказ успешно оплачен',
            f'Ваш заказ №{order.id} на сумму {order.get_total_cost():.2f} руб. успешно оплачен.',
            'noreply@my-shop.com', # from_email
            [order.email], # recipient_list
            fail_silently=False, # Set to True in production if you don't want to crash on email errors
        )

        return redirect('app:payment_done')
    
    return render(request, 'app/dummy_payment.html', {'order': order, 'title': 'Подтверждение оплаты'})

def payment_done(request):
    return render(request, 'app/payment_done.html', {'title': 'Оплата прошла успешно'})


@csrf_exempt
def yookassa_webhook(request):
    try:
        ip = request.META.get('HTTP_X_FORWARDED_FOR')
        if not Webhook.is_source_in_trusted_ips(ip):
            return HttpResponse(status=400)

        event_json = json.loads(request.body)
        notification_object = Webhook(event_json)
        response_object = notification_object.object

        if response_object.status == 'succeeded':
            order_id = int(response_object.metadata['order_id'])
            order = get_object_or_404(Order, id=order_id)
            if order.get_total_cost() == float(response_object.amount.value):
                order.paid = True
                order.save()
        
        return HttpResponse(status=200)

    except Exception as e:
        # For debugging purposes
        logging.error(f"YooKassa webhook error: {e}")
        return HttpResponse(status=400)


@login_required
def profile(request):
    orders = Order.objects.filter(user=request.user).order_by('-created')
    return render(request, 'app/profile.html', {'orders': orders, 'title': 'Ваш профиль'})


@require_POST
@login_required
def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if order.status == 'processing':
        order.status = 'cancelled'
        order.save()
    return redirect('app:profile')



def product_search(request):
    query = request.GET.get('q')
    results = []
    if query:
        results = Product.objects.filter(Q(name__iregex=query) | Q(description__iregex=query)).annotate(avg_rating=Avg('reviews__rating'))
    
    return render(request,
                  'app/search.html',
                  {'query': query,
                   'results': results,
                   'title': 'Результаты поиска'})

# Blog views
def post_list(request):
    posts = Post.objects.all()
    return render(request, 'app/post_list.html', {'posts': posts, 'title': 'Блог'})

def post_detail(request, slug):
    post = get_object_or_404(Post, slug=slug)
    comments = post.comments.filter(active=True)
    new_comment = None
    if request.method == 'POST':
        comment_form = CommentForm(data=request.POST)
        if comment_form.is_valid():
            new_comment = comment_form.save(commit=False)
            new_comment.post = post
            new_comment.author = request.user
            new_comment.save()
            return redirect(post.get_absolute_url())
    else:
        comment_form = CommentForm()
    return render(request, 'app/post_detail.html', {'post': post,
                                                   'comments': comments,
                                                   'new_comment': new_comment,
                                                   'comment_form': comment_form,
                                                   'title': post.title})

@user_passes_test(lambda u: u.is_staff)
def post_create(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            new_post = form.save(commit=False)
            new_post.author = request.user
            new_post.save()
            return redirect(new_post.get_absolute_url())
    else:
        form = PostForm()
    return render(request, 'app/post_form.html', {'form': form, 'title': 'Создать пост'})
