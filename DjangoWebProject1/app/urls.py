from django.urls import path, re_path
from . import views

app_name = 'app'

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('category/<slug:category_slug>/', views.product_list, name='product_list_by_category'),
    path('product/<int:id>/<slug:slug>/', views.product_detail, name='product_detail'),
    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/add/<int:product_id>/', views.cart_add, name='cart_add'),
    path('cart/remove/<int:product_id>/', views.cart_remove, name='cart_remove'),
    path('create/', views.order_create, name='order_create'),
    path('order/cancel/<int:order_id>/', views.cancel_order, name='cancel_order'),
    path('profile/', views.profile, name='profile'),
    path('search/', views.product_search, name='product_search'),
    path('review/delete/<int:review_id>/', views.delete_review, name='delete_review'),
    # Payment URLs
    path('payment/process/<int:order_id>/', views.payment_process, name='payment_process'),
    path('payment/done/', views.payment_done, name='payment_done'),
    path('payment/webhook/', views.yookassa_webhook, name='yookassa_webhook'),
    path('payment/dummy/<int:order_id>/', views.dummy_payment, name='dummy_payment'),

    # Blog URLs
    path('blog/', views.post_list, name='post_list'),
    path('blog/create/', views.post_create, name='post_create'),
    re_path(r'^blog/(?P<slug>[-\w]+)/$', views.post_detail, name='post_detail'),
]
