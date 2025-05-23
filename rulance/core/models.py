from django.contrib.auth.models import AbstractUser, Group, Permission  
from django.db import models
from django.conf import settings
from django.urls import reverse
import os
import uuid

class User(AbstractUser):
    ROLE_CHOICES = [
        ('Freelancer', 'Фрилансер'),
        ('Client', 'Заказчик'),
    ]
    
    full_name = models.CharField("Полное имя", max_length=100)
    email = models.EmailField("Email", unique=True)
    role = models.CharField("Роль", max_length=20, choices=ROLE_CHOICES, default='Freelancer')
    avatar = models.ImageField("Аватар", upload_to='avatars/', null=True, blank=True, default='avatars/default.png')
    balance = models.DecimalField("Баланс", max_digits=10, decimal_places=2, default=0.00)
    groups = models.ManyToManyField(
        Group,
        verbose_name='Группы',
        blank=True,
        related_name='core_users',  
        help_text='Группы, к которым принадлежит пользователь',
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name='Права доступа',
        blank=True,
        related_name='core_users_permissions', 
        help_text='Права доступа пользователя',
    )

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return self.username
    
class Payment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_intent_id = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Платёж"
        verbose_name_plural = "Платежи"
    
class Sphere(models.Model):
    name = models.CharField("Название категории", max_length=255)

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

    def __str__(self):
        return self.name


class SphereType(models.Model):
    sphere = models.ForeignKey(Sphere, on_delete=models.CASCADE, verbose_name="Категория")
    name = models.CharField("Название подкатегории", max_length=255)

    class Meta:
        verbose_name = "Подкатегория"
        verbose_name_plural = "Подкатегории"

    def __str__(self):
        return f"{self.sphere.name} → {self.name}"

class Order(models.Model):
    STATUS_CHOICES = [
        ('Open', 'Открыт'),
        ('InWork', 'В работе'),
        ('Completed', 'Завершён'),
        ('Cancelled', 'Отменён'),
        ('Deleted', 'Удалён'),
    ]

    title = models.CharField("Заголовок", max_length=200)
    description = models.TextField("Описание")
    
    sphere = models.ForeignKey(
        Sphere, 
        on_delete=models.CASCADE, 
        verbose_name="Категория"
    )
    sphere_type = models.ForeignKey(
        SphereType, 
        on_delete=models.CASCADE, 
        verbose_name="Подкатегория"
    )
    
    price = models.DecimalField(
        "Цена",
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    is_negotiable = models.BooleanField("Договорная цена", default=False)
    created_at = models.DateTimeField("Создан", auto_now_add=True)
    status = models.CharField(
        "Статус",
        max_length=20,
        choices=STATUS_CHOICES,
        default='Open'
    )
    reason_of_cancel = models.TextField(null=True, blank=True)
    client = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Заказчик")
    updated_at = models.DateTimeField(auto_now=True)
    has_review = models.BooleanField("Отзыв оставлен", default=False)

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"

    def __str__(self):
        return self.title
    

class Portfolio(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='portfolio',
        verbose_name='Фрилансер'
    )
    sphere = models.ForeignKey(
        'Sphere',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Категория'
    )
    sphere_type = models.ForeignKey(
        'SphereType',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Подкатегория'
    )
    less_than_year = models.BooleanField(
        'Опыт меньше года',
        default=False
    )
    years_experience = models.PositiveIntegerField(
        'Опыт работы (лет)',
        null=True,
        blank=True
    )
    hourly_rate = models.DecimalField(
        'Ставка в час (₽)',
        max_digits=10,
        decimal_places=2
    )
    monthly_rate = models.DecimalField(
        'Ставка в месяц (₽)',
        max_digits=10,
        decimal_places=2
    )
    description = models.TextField('Описание опыта')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Портфолио'
        verbose_name_plural = 'Портфолио'

    def __str__(self):
        return f'Портфолио {self.user.username}'
    
def order_file_path(instance, filename):
    ext = filename.split('.')[-1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    return os.path.join('order_files', filename)

class OrderFile(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='files',
        verbose_name='Заказ'
    )
    file = models.FileField(
        upload_to=order_file_path,
        verbose_name='Файл'
    )

    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Файл заказа'
        verbose_name_plural = 'Файлы заказа'

    def __str__(self):
        return f"{self.order.title} — {os.path.basename(self.file.name)}"
    

class Response(models.Model):
    STATUS_CHOICES = [
        ('Pending',  'Ожидает'),
        ('Accepted', 'Принят'),
        ('Rejected', 'Отклонён'),
    ]

    order = models.ForeignKey(
        'Order',
        on_delete=models.CASCADE,
        related_name='responses',
        verbose_name='Заказ'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='responses',
        verbose_name='Фрилансер'
    )
    description     = models.TextField('Почему именно вы')
    term            = models.PositiveIntegerField('Срок исполнения (дни)')
    responser_price = models.DecimalField('Ваша цена (₽)', max_digits=10, decimal_places=2)
    status          = models.CharField('Статус', max_length=10, choices=STATUS_CHOICES, default='Pending')
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Отклик'
        verbose_name_plural = 'Отклики'
        unique_together = [('order','user')]  

    def __str__(self):
        return f'Отклик #{self.pk} by {self.user.username} на {self.order.title}'

class Notification(models.Model):
    user       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    verb       = models.CharField("Текст уведомления", max_length=255)
    link       = models.CharField("URL или имя пути", max_length=255, blank=True,
                                 help_text="Можно передать reverse('viewname', args=[...])")
    is_read    = models.BooleanField("Прочитано", default=False)
    created_at = models.DateTimeField("Создано", auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Уведомление'
        verbose_name_plural = 'Уведомления'

    def __str__(self):
        return f"{self.verb} ({'прочитано' if self.is_read else 'новое'})"

    def get_absolute_url(self):
        try:
            return reverse(self.link)
        except:
            return self.link
        
class Chat(models.Model):
    order = models.ForeignKey('Order', on_delete=models.CASCADE, related_name='chats')
    freelancer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='freelancer_chats')
    client = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='client_chats')
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Chat {self.order.id} between {self.client} and {self.freelancer}"

class Message(models.Model):
    SYSTEM = 'system'
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_system = models.BooleanField(default=False)
    extra_data = models.JSONField(blank=True, null=True, default=dict)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.sender} @ {self.timestamp:%Y-%m-%d %H:%M}"
    
class Review(models.Model):
    RATING_CHOICES = [
        ('Bad', 'Плохо'),
        ('Average', 'Средне'),
        ('Excellent', 'Отлично'),
    ]

    order = models.OneToOneField(
        'Order',
        on_delete=models.CASCADE,
        related_name='review',
        verbose_name='Заказ'
    )
    freelancer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews_received',
        verbose_name='Фрилансер',
        
    )
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews_given',  
        verbose_name='Клиент'
    )
    rating = models.CharField('Оценка', max_length=10, choices=RATING_CHOICES)
    text = models.TextField('Текст отзыва')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'

    def __str__(self):
        return f'Отзыв на заказ {self.order.title} от {self.client.username} для {self.freelancer.username}'