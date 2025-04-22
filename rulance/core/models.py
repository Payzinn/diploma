from django.contrib.auth.models import AbstractUser, Group, Permission  
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = [
        ('Freelancer', 'Фрилансер'),
        ('Client', 'Заказчик'),
    ]
    
    full_name = models.CharField("Полное имя", max_length=100)
    email = models.EmailField("Email", unique=True)
    role = models.CharField("Роль", max_length=20, choices=ROLE_CHOICES, default='Freelancer')
    avatar = models.ImageField("Аватар", upload_to='avatars/', null=True, blank=True, default='avatars/default.png')
    
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
    
class Sphere(models.Model):
    """
    Модель для категорий (например, Разработка, Дизайн, Маркетинг).
    """
    name = models.CharField("Название категории", max_length=255)

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

    def __str__(self):
        return self.name


class SphereType(models.Model):
    """
    Модель для подкатегорий (например, Сайты под ключ, Бэкенд и т.д.).
    """
    sphere = models.ForeignKey(Sphere, on_delete=models.CASCADE, verbose_name="Категория")
    name = models.CharField("Название подкатегории", max_length=255)

    class Meta:
        verbose_name = "Подкатегория"
        verbose_name_plural = "Подкатегории"

    def __str__(self):
        return f"{self.sphere.name} → {self.name}"

class Order(models.Model):
    STATUS_CHOICES = [
        ('Открыт', 'Открыт'),
        ('В работе', 'В работе'),
        ('Завершён', 'Завершён'),
        ('Отменён', 'Отменён'),
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
        default='Открыт'
    )
    client = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Заказчик")

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"

    def __str__(self):
        return self.title