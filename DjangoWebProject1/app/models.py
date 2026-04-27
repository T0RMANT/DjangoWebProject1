from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.contrib.auth.models import User
from django.core.mail import send_mail

class Category(models.Model):
    name = models.CharField(max_length=200, db_index=True, verbose_name="Категория")
    slug = models.SlugField(max_length=200, unique=True)

    class Meta:
        ordering = ('name',)
        verbose_name = 'категория'
        verbose_name_plural = 'категории'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('app:product_list_by_category', args=[self.slug])

class Product(models.Model):
    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE, verbose_name="Категория")
    name = models.CharField(max_length=200, db_index=True, verbose_name="Название")
    slug = models.SlugField(max_length=200, db_index=True)
    main_image = models.ImageField(upload_to='products/%Y/%m/%d', blank=True, null=True, verbose_name="Главное изображение")
    description = models.TextField(blank=True, verbose_name="Описание")
    scale = models.CharField(max_length=50, blank=True, verbose_name="Масштаб")
    brand = models.CharField(max_length=100, blank=True, verbose_name="Производитель")
    material = models.CharField(max_length=100, blank=True, verbose_name="Материал")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")
    available = models.BooleanField(default=True, verbose_name="В наличии")
    created = models.DateTimeField(auto_now_add=True, verbose_name="Добавлена")
    updated = models.DateTimeField(auto_now=True, verbose_name="Обновлена")

    class Meta:
        ordering = ('name',)
        indexes = [
            models.Index(fields=['id', 'slug']),
        ]
        verbose_name = 'товар'
        verbose_name_plural = 'товары'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('app:product_detail', args=[self.id, self.slug])

class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE, verbose_name="Товар")
    image = models.ImageField(upload_to='products/%Y/%m/%d', blank=True, null=True, verbose_name="Изображение")

    def __str__(self):
        return f"Изображение для {self.product.name}"

class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews', verbose_name="Товар")
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Автор")
    rating = models.IntegerField(default=5, verbose_name="Рейтинг")
    text = models.TextField(verbose_name="Текст отзыва")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        ordering = ('-created_at',)
        verbose_name = 'отзыв'
        verbose_name_plural = 'отзывы'

    def __str__(self):
        return f'Отзыв от {self.author} на {self.product}'

class Order(models.Model):
    STATUS_CHOICES = (
        ('processing', 'В обработке'),
        ('shipped', 'Отправлен'),
        ('delivered', 'Доставлен'),
        ('cancelled', 'Отменен'),
        ('completed', 'Завершен'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders', null=True, blank=True, verbose_name='Пользователь')
    first_name = models.CharField(max_length=50, verbose_name='Имя')
    last_name = models.CharField(max_length=50, verbose_name='Фамилия')
    email = models.EmailField(verbose_name='Email')
    address = models.CharField(max_length=250, verbose_name='Адрес')
    postal_code = models.CharField(max_length=20, verbose_name='Почтовый индекс')
    city = models.CharField(max_length=100, verbose_name='Город')
    created = models.DateTimeField(auto_now_add=True, verbose_name='Создан')
    updated = models.DateTimeField(auto_now=True, verbose_name='Обновлен')
    paid = models.BooleanField(default=False, verbose_name='Оплачен')
    yookassa_payment_id = models.CharField(max_length=150, blank=True, verbose_name='ID платежа ЮKassa')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='processing', verbose_name='Статус')

    DELIVERY_CHOICES = (
        ('cdek', 'СДЭК'),
        ('russian_post', 'Почта России'),
        ('sber_logistics', 'Сбер Логистика'),
    )
    delivery_service = models.CharField(max_length=20, choices=DELIVERY_CHOICES, default='cdek', verbose_name='Служба доставки')
    cdek_point = models.CharField(max_length=250, blank=True, null=True, verbose_name='Пункт выдачи СДЭК')
    post_office_address = models.CharField(max_length=250, blank=True, null=True, verbose_name='Адрес почтового отделения')

    
    class Meta:
        ordering = ('-created',)
        verbose_name = 'заказ'
        verbose_name_plural = 'заказы'

    def __str__(self):
        return f'Order {self.id}'

    def get_total_cost(self):
        return sum(item.get_cost() for item in self.items.all())

    def save(self, *args, **kwargs):
        # Store the original status
        if self.pk:
            original = Order.objects.get(pk=self.pk)
            original_status = original.status
        else:
            original_status = None

        super().save(*args, **kwargs)

        # Check if status has changed to 'delivered'
        if self.status == 'delivered' and original_status != 'delivered':
            # Send email to user
            send_mail(
                f'Ваш заказ №{self.id} доставлен',
                f'''Здравствуйте, {self.first_name}!

Ваш заказ №{self.id} был доставлен. Спасибо за покупку!''',
                'noreply@my-shop.com',
                [self.email],
                fail_silently=False,
            )


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='order_items', on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return str(self.id)

    def get_cost(self):
        return self.price * self.quantity

class Post(models.Model):
    title = models.CharField(max_length=200, verbose_name="Заголовок")
    slug = models.SlugField(max_length=200, unique=True, help_text="Используйте только латиницу, цифры, подчеркивания или дефисы.", verbose_name="Слаг")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blog_posts', verbose_name="Автор")
    image = models.ImageField(upload_to='posts/%Y/%m/%d', blank=True, verbose_name="Изображение")
    text = models.TextField(verbose_name="Текст")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'пост'
        verbose_name_plural = 'посты'

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('app:post_detail', args=[self.slug])

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments', verbose_name="Пост")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='post_comments', verbose_name="Автор")
    text = models.TextField(verbose_name="Текст комментария")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    active = models.BooleanField(default=True, verbose_name="Активен")

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'комментарий'
        verbose_name_plural = 'комментарии'

    def __str__(self):
        return f'Комментарий от {self.author} к {self.post}'
