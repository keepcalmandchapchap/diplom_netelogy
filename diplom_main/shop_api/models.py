from django.db import models
from django.utils import timezone
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.utils.translation import gettext_lazy as _

from .managers import UserManager

USER_TYPE_INFO = (
    ('phone', 'Номер телефона'),
    ('sex', 'Пол'),
    ('birthdate', 'День рождения'),
)

STATE_CHOICES = (
    ('basket', 'Корзина'),
    ('created', 'Заказ создан'),
    ('collecting', 'Собирается'),
    ('collected', 'Собран'),
    ('shipped', 'Отгружен'),
    ('delivered', 'Доставлен'),
    ('canceled', 'Отказ'),
)


class User(AbstractBaseUser, PermissionsMixin):
    '''
    Переопределлная базовая модель django под авторизацию по email
    '''
    email = models.EmailField(_('email'), unique=True)
    first_name = models.CharField(_('name'), max_length=30, blank=True)
    last_name = models.CharField(_('surame'), max_length=30, blank=True)
    date_joined = models.DateField(_('registered'), auto_now_add=True)
    is_active = models.BooleanField(_('is_active'), default=False)
    is_staff = models.BooleanField(_('is_staff'), default=False)  # оставил is_staff для корректной работы админки
    is_superuser = models.BooleanField(_('is_superuser'), default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def get_full_info(self):
        full_info = {
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'date_joined': self.date_joined,
            'is_active': self.is_active,
            'is_staff': self.is_staff,
        }
        return full_info

    def __str__(self):
        return f'{self.email}'

    def get_full_name(self):
        return f'{self.first_name} {self.last_name} {self.email}'

    def get_id(self):
        return {'id': self.id}


class UserInfo(models.Model):
    '''
    Информация о пользователях
    '''
    user = models.ForeignKey('User', on_delete=models.CASCADE, null=False, related_name='info_as_user', verbose_name='Пользователь')
    type_info = models.CharField(choices=USER_TYPE_INFO, null=False, verbose_name='Тип характеристики')
    value_info = models.CharField(max_length=120, null=False, verbose_name='Значение характеристики')

    class Meta:
        verbose_name = 'Информация о пользователе'
        verbose_name_plural = 'Информация о пользователях'
        unique_together = ['user', 'type_info', ]


class Position(models.Model):
    '''
    Должности
    '''
    name = models.CharField(max_length=120, unique=True, null=False, verbose_name='Название должности')

    class Meta:
        verbose_name = 'Должность'
        verbose_name_plural = 'Должности'

    def __str__(self):
        return f'{self.name}'


class StaffInfo(models.Model):
    '''
    Информация о сотрудниках
    '''
    user = models.OneToOneField('User', on_delete=models.CASCADE, related_name='info_as_staff', verbose_name='Пользователь')
    manager = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, related_name='info_as_manager', verbose_name='Руководитель')
    position = models.ForeignKey('Position', on_delete=models.SET_NULL, null=True, related_name='staff', verbose_name='Должность')
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    description = models.TextField(null=True, blank=True, verbose_name='Комментарий')

    class Meta:
        verbose_name = 'Информация о сотруднике'
        verbose_name_plural = 'Информация о сотрудниках'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['manager']),
            models.Index(fields=['position']),
        ]

    def __str__(self):
        return f'{self.position if self.position else 'Без должности'} {self.user.first_name} {self.user.last_name}'


class Address(models.Model):
    '''
    Адреса
    '''
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='address', verbose_name='Пользователь')
    city = models.CharField(max_length=100, verbose_name='Город')
    street = models.CharField(max_length=300, verbose_name='Улица')
    house = models.CharField(max_length=10, verbose_name='Дом')
    building = models.CharField(max_length=10, null=True, blank=True, verbose_name='Строение')
    floor = models.PositiveIntegerField(null=True, blank=True, verbose_name='Этаж')
    appartment = models.PositiveIntegerField(verbose_name='Квартира')

    class Meta:
        verbose_name = 'Адрес'
        verbose_name_plural = 'Адреса'
        unique_together = ['city', 'street', 'house', 'building', 'appartment']

    def __str__(self):
        return f'Город: {self.city}, Улица: {self.street}, Дом: {self.house}, \
Стр: {self.building if self.building else 'Не указан'}, Квартира: {self.appartment}, Этаж: {self.floor if self.floor else None}'

    def get_full_address(self):
        return {
            'city': self.city,
            'street': self.street,
            'house': self.house,
            'building': f'{self.building if self.building else None}',
            'appartment': self.appartment,
            'floor': f'{self.floor if self.floor else None}'
        }


class VendorInfo(models.Model):
    '''
    Информация о поставщиках
    '''
    user = models.OneToOneField('User', on_delete=models.CASCADE, related_name='info_as_vendor', verbose_name='Пользователь')
    name = models.CharField(max_length=300, unique=True, verbose_name='Название')
    inn = models.CharField(max_length=12, unique=True, verbose_name='ИНН')
    description = models.TextField(null=True, blank=True, verbose_name='Описание')

    class Meta:
        verbose_name = 'Иноформация о сотруднике'
        verbose_name_plural = 'Информация о сотрудниках'

    def __str__(self):
        return f'Пользователь: {self.user.email}, компания: {self.name}, ИНН: {self.inn}, адрес: {self.address.get_full_address()}'

    def get_full_info(self):
        return {
            'user': self.user.email,
            'name': self.name,
            'inn': self.inn,
            'description': self.description,
            'address': self.address.get_full_info()
        }


class Order(models.Model):
    '''
    Заказ
    '''
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='order', verbose_name='Пользователь')
    address = models.ForeignKey('Address', null=True, on_delete=models.PROTECT, related_name='order', verbose_name='Адрес')
    state = models.CharField(choices=STATE_CHOICES, default='basket', verbose_name='Статус')
    comment = models.TextField(null=True, blank=True, verbose_name='Комментарий')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Общая сумма')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Время создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Время обновления')
    closed_at = models.DateTimeField(null=True, blank=True, verbose_name='Время закрытия')
    items = models.ManyToManyField('Item', through='OrderItem', verbose_name='Товары')

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['state']),
            models.Index(fields=['user', 'state'])
        ]

    def __str__(self):
        return f'ID заказа {self.id}. Дата создания: {self.create_at if self.created_at else 'Заказ в состоянии "Корзина;Закрыт;Доставлен"'}. Статус: {self.state}.'

    def save(self, *args, **kwargs):
        if self.state in ['delivered', 'canceled'] and not self.closed_at:
            self.closed_at = timezone.now()
        return super().save(*args, **kwargs)

    def is_active(self):
        return self.state not in ['delivered', 'canceled']


class Item(models.Model):
    '''
    Товар
    '''
    name = models.CharField(max_length=150, unique=True, verbose_name='Название')
    vendor = models.ForeignKey('User', on_delete=models.PROTECT, related_name='items', verbose_name='Поставщик', help_text='Ссылка на пользователя, так как думаю так логичнее')
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Цена')
    quantity = models.PositiveIntegerField(verbose_name='Количество')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Время обновления')
    is_active = models.BooleanField(default=True, verbose_name='В продаже')

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'
        indexes = [
            models.Index(fields=['vendor']),
        ]

    def __str__(self):
        vendor_info = getattr(self.vendor, 'info_as_vendor', None)
        vendor_info = vendor_info.name if vendor_info else 'Поставищка нет'
        return f'{self.name} - Поставищк: {vendor_info}, цена {self.price}, кол-во {self.quantity}'

    def get_full_info(self):
        vendor_info = getattr(self.vendor, 'info_as_vendor', None)
        return {
            'name': self.name,
            'vendor': {
                'id': self.vendor.id,
                'name': vendor_info.name if vendor_info else None,
                'inn': vendor_info.inn if vendor_info else None,
            },
            'price': self.price,
            'quantity': self.quantity,
            'updated_at': self.updated_at
        }

    def decrease_quantity(self, amount):
        if amount > self.quantity:
            raise ValueError('Недостаточное кол-во товара')
        self.quantity -= amount
        self.save()

    def amount(self):
        return self.quantity

    def available(self):
        return self.quantity > 0


class OrderItem(models.Model):
    order = models.ForeignKey('Order', on_delete=models.CASCADE, verbose_name='Заказ', related_name='order_item')
    item = models.ForeignKey('Item', on_delete=models.PROTECT, verbose_name='Товар', related_name='item_order')
    quantity = models.PositiveIntegerField(verbose_name='Количество')
    price_at_order = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена на момент заказа')

    class Meta:
        unique_together = ['order', 'item']
        indexes = [
            models.Index(fields=['order']),
            models.Index(fields=['item'])
        ]

    def save(self, *args, **kwargs):
        if not self.pk:
            self.price_at_order = self.item.price
        super().save(*args, **kwargs)

    def total_price(self):
        return self.price_at_order * self.quantity


class Category(models.Model):
    '''
    Категории
    '''
    name = models.CharField(max_length=100, unique=True, null=False, verbose_name='Название')
    items = models.ManyToManyField('Item', related_name='categories', verbose_name='Товары')

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'

    def give_items(self):
        return {'name': self.items.id}


class ItemInfo(models.Model):
    '''
    Информация о товарах
    '''
    item = models.ForeignKey('Item', on_delete=models.CASCADE, verbose_name='Товар', related_name='info')
    type_info = models.CharField(max_length=150, unique=False, verbose_name='Тип информации')
    value_info = models.CharField(max_length=300, unique=False, default='Не указано', verbose_name='Значение информации')

    class Meta:
        verbose_name = 'Информация о товаре'
        verbose_name_plural = 'Информация о товарах'
