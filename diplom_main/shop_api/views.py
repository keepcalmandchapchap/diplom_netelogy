import json
import csv
import datetime

from django.forms import ValidationError
from django.urls import reverse
from django.db import transaction
from django.template.loader import render_to_string
from django.conf import settings
from django.core.mail import send_mail
from django.utils.html import strip_tags
from django.contrib.auth.models import Group
from rest_framework import status
from rest_framework.parsers import MultiPartParser
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.exceptions import NotFound, PermissionDenied

from django_filters.rest_framework import DjangoFilterBackend

from .serializers import RegisterSerializer, UserInfoSerializer, LoginSerializer, PositionSerializer, StaffInfoSerializer, AddressClientSerializer
from .serializers import AddressManagerSerializer, VendorInfoSerializer, ItemSerializer, CategorySerializer, OrderSerializer
from .models import UserInfo, Position, StaffInfo, Address, VendorInfo, Item, Category, Order, OrderItem
from .permissions import IsInGroups, IsVendorOrManager
from .utils import send_customer_order_confirmation, generate_and_send_invoice_pdf, send_order_delivered_email, generate_activation_token, validate_activation_token


def gen_error(serializer, error_status: status):
    if not serializer.is_valid():
        return Response(
            {
                'status': 'error',
                'errors': serializer.errors,
            }, status=error_status)


class RegisterView(APIView):
    '''
    Представление для регистрации стандартного пользователя
    '''
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            token = generate_activation_token(user)

            activation_link = request.build_absolute_uri(
                reverse('activate_account', args=[token])
            )

            subject = 'Подтвердите ваш email'
            html_message = render_to_string('emails/activation_email.html', {
                'user': user,
                'activation_link': activation_link
            })
            plain_message = strip_tags(html_message)
            from_email = settings.DEFAULT_FROM_EMAIL
            to_email = [user.email]

            send_mail(subject, plain_message, from_email, to_email, html_message=html_message)

            return Response({
                'status': 'success',
                'message': 'Проверьте почту для подтверждения email.',
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ActivateAccountView(APIView):
    def get(self, request, token):
        user = validate_activation_token(token)
        if user and not user.is_active:
            user.is_active = True
            user.save(update_fields=['is_active'])
            return Response({
                'status': 'success',
                'message': 'Ваш аккаунт успешно активирован!'
            }, status=status.HTTP_200_OK)
        elif user and user.is_active:
            return Response({
                'status': 'warning',
                'message': 'Аккаунт уже активирован.'
            }, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({
                'status': 'error',
                'message': 'Неверный или просроченный токен.'
            }, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    '''
    Вью для входа
    '''
    permission_classes = []
    authentication_classes = []

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})

        gen_error(serializer, status.HTTP_401_UNAUTHORIZED)

        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        response_data = {
            'status': 'success'
        }
        headers = {
            'Authorization': f'Bearer {str(refresh.access_token)}',
            'X-Refresh-Token': str(refresh)
        }
        return Response(response_data, headers=headers, status=status.HTTP_200_OK)


class UserInfoOwnerView(ModelViewSet):
    serializer_class = UserInfoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserInfo.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        type_info = request.data.get('type_info')
        if UserInfo.objects.filter(user=request.user, type_info=type_info).exists():
            return Response({
                'status': 'error', 'message': 'Запись с таким типом информации уже существует'
            }, status=status.HTTP_400_BAD_REQUEST)
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)

        type_info = request.data.get('type_info', instance.type_info)

        if UserInfo.objects.filter(user=request.user, type_info=type_info).exclude(pk=instance.pk).exists():
            return Response({
                'status': 'error',
                'message': 'Запись с таким типом информации уже существует'
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({
            'status': 'success'
        }, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({
            'status': 'success',
            'message': 'Запись успешно удалена'
        }, status=status.HTTP_200_OK)

    def perform_destroy(self, instance):
        instance.delete()


class PositionView(ModelViewSet):
    queryset = Position.objects.all()
    serializer_class = PositionSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsInGroups(['employee_base', 'manager_base'])]
        if self.request.method in ['POST', 'PUT', 'DELETE']:
            return [IsInGroups(['manager_base'])]
        return super().get_permissions()


class StaffInfoView(ModelViewSet):
    serializer_class = StaffInfoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return StaffInfo.objects.all()

    def get_object(self):
        user_id = self.kwargs.get('pk')
        queryset = self.get_queryset()

        try:
            obj = queryset.get(user_id=user_id)
            self.check_object_permissions(self.request, obj)
            return obj
        except StaffInfo.DoesNotExist:
            raise NotFound('Запись указанного пользователя не найдена.')

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        else:
            return [IsAuthenticated(), IsInGroups(['manager_base'])]

    @action(detail=True, methods=['patch'], permission_classes=[IsAuthenticated, IsInGroups(['manager_base'])])
    def dissmiss(self, request, pk=None):
        staff_info = self.get_object()
        staff_info.is_active = False
        description = request.data.get('description')
        if description:
            staff_info.description = description
        staff_groups = Group.objects.filter(user=staff_info.user)
        for staff_group in staff_groups:
            staff_info.user.groups.remove(staff_group)
        staff_info.save()
        return Response({
            'status': 'success',
            'message': f'Сотрудник {staff_info.user.email} уволен'})


class AddressClientView(ModelViewSet):
    serializer_class = AddressClientSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)

    def get_object(self):
        queryset = self.get_queryset()
        pk = self.kwargs.get('pk')
        obj = queryset.get(pk=pk)
        self.check_object_permissions(self.request, obj)
        return obj

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class AddressManagerView(ModelViewSet):
    serializer_class = AddressManagerSerializer

    def get_permissions(self):
        return [IsAuthenticated(), IsInGroups(['manager_base'])]

    def get_queryset(self):
        return Address.objects.all()


class VendorInfoView(ModelViewSet):
    serializer_class = VendorInfoSerializer

    def get_permissions(self):
        if self.action in ['change_description']:
            return [IsAuthenticated(), IsInGroups(['vendor_base'])]
        else:
            return [IsAuthenticated(), IsInGroups(['manager_base'])]

    def get_queryset(self):
        return VendorInfo.objects.all()

    def get_object(self):
        user_id = self.kwargs.get('pk')
        queryset = self.get_queryset()

        try:
            obj = queryset.get(user_id=user_id)
            self.check_object_permissions(self.request, obj)
            return obj
        except VendorInfo.DoesNotExist:
            raise NotFound('Запись указанного поставщика не найдена.')

    @action(detail=False, methods=['patch'])
    def change_description(self, request):
        vendor_info = VendorInfo.objects.get(user=request.user.id)
        new_description = request.data.get('description')
        if not new_description:
            return Response({
                'status': 'error', 'message': 'Не указано новое описание'
            }, status=status.HTTP_400_BAD_REQUEST)
        vendor_info.description = new_description
        vendor_info.save()
        return Response({
            'status': 'success'
        }, status=status.HTTP_200_OK)


class ItemView(ModelViewSet):
    serializer_class = ItemSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    searCLEARch_fields = ['name', 'description', 'vendor', 'categories_name']
    ordering_fields = ['price', 'updated_at', 'vendor', 'is_active', 'quantity']

    def get_permissions(self):
        if self.action in ['new_item', 'change_price', 'activate', 'deactivate', ]:
            return [IsAuthenticated(), IsInGroups(['vendor_base'])]
        elif self.action in ['list', 'retrieve', ]:
            return []
        elif self.action in ['add_to_basket', ]:
            return [IsAuthenticated()]
        else:
            return [IsAuthenticated(), IsInGroups(['manager_base'])]

    def get_queryset(self):
        queryset = Item.objects.all()

        category_id = self.request.query_params.get('category')
        if category_id:
            queryset = Item.objects.filter(categories__id=category_id)

        category_ids = self.request.query_params.get('categories')
        if category_ids:
            category_list = category_ids.split(',')
            queryset = Item.objects.filter(categories__id__in=category_list).distinct()

        return queryset

    def perform_create(self, serializer):
        return serializer.save(vendor=self.request.user)

    @action(detail=False, methods=['post'])
    def new_item(self, request):
        mutable_data = request.data.copy()
        mutable_data['vendor'] = request.user.id
        serializer = self.get_serializer(data=mutable_data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({'status': 'success', }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['patch'], permission_classes=[IsAuthenticated, IsInGroups(['vendor_base'])])
    def change_price(self, request, pk=None):
        item = self.get_object()

        if item.vendor != request.user:
            raise PermissionDenied('Вы не имеете право взаимодействовать с этим товаром.')

        serializer = self.get_serializer(item, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'status': 'success'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['patch'])
    def deactivate(self, request, pk=None):
        item = self.get_object()

        if item.vendor != request.user:
            raise PermissionDenied('Вы не имеете право взаимодействовать с этим товаром.')

        if item.is_active is True:
            item.is_active = False
        else:
            return Response({'status': 'error',
                             'message': 'Товар уже снят с продажи.'})
        item.save()
        return Response({'status': 'success'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['patch'])
    def activate(self, request, pk=None):
        item = self.get_object()

        if item.vendor != request.user:
            raise PermissionDenied('Вы не имеете право взаимодействовать с этим товаром.')

        if item.is_active is False:
            item.is_active = True
        else:
            return Response({'status': 'error',
                             'message': 'Товар уже в продаже.'})
        item.save()
        return Response({'status': 'success'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def add_to_basket(self, request, pk):
        quantity = request.data.get('quantity')

        if not quantity:
            quantity = 1

        try:
            item = Item.objects.get(pk=pk)
        except Item.DoesNotExist:
            raise NotFound('Указанный товар не найден')

        basket, created = Order.objects.get_or_create(user=self.request.user, state='basket')

        order_item, created = OrderItem.objects.get_or_create(item=item, order=basket, defaults={'quantity': quantity})

        if not created:
            order_item.quantity += int(quantity)
            order_item.save()

        basket.total_price = sum(i.total_price() for i in basket.order_item.all())
        basket.save()

        return Response({
            'status': 'success',
            'data': self.request.data
        }, status=status.HTTP_201_CREATED)


class CategoryView(ModelViewSet):
    serializer_class = CategorySerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return []
        else:
            return [IsAuthenticated(), IsInGroups(['employee_base', 'manager_base', ])]

    def get_queryset(self):
        return Category.objects.all()

    @action(detail=False, methods=['POST'])
    def add_item(self, request):
        category_id = request.data.get('category')
        item_id = request.data.get('item')

        if not category_id:
            return Response({
                'status': 'error',
                'message': 'Не указана категория'},
                status=status.HTTP_400_BAD_REQUEST)

        if not item_id:
            return Response({
                'status': 'error',
                'message': 'Не указан товар'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            category_obj = Category.objects.get(id=category_id)
        except Category.DoesNotExist:
            raise NotFound('Категория не найдена')

        try:
            item_obj = Item.objects.get(id=item_id)
        except Item.DoesNotExist:
            raise NotFound('Товар не найден')

        category_obj.items.add(item_obj)

        return Response({
            'status': 'success',
            'data': request.data,
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def add_items(self, request):
        category_id = request.data.get('category')
        items_ids = request.data.get('items')

        if not category_id:
            return Response({
                'status': 'error',
                'message': 'В запросе не указана категория'},
                status=status.HTTP_400_BAD_REQUEST)

        if not items_ids:
            return Response({
                'status': 'error',
                'message': 'В запросе не указаны товары!'
            }, status=status.HTTP_400_BAD_REQUEST)

        items_ids_json = json.loads(items_ids)

        try:
            category_obj = Category.objects.get(id=category_id)
        except Category.DoesNotExist:
            raise NotFound('Категория не найдена')

        items_objs = Item.objects.filter(id__in=items_ids_json)

        category_obj.items.add(*items_objs)

        return Response({
            'status': 'success',
            'data': request.data
        }, status=status.HTTP_200_OK)


def __get_order_and_change_state(pk, state):
    try:
        order_obj = Order.objects.get(pk=pk)
    except Order.DoesNotExist:
        raise NotFound('Указанный заказ не найден.')

    order_obj.state = f'{state}'
    order_obj.save()

    return Response({
        'status': 'success',
        'message': f'Статус успешно обновлен на "{state}"'
    }, status=status.HTTP_200_OK)


class OrderView(ModelViewSet):
    serializer_class = OrderSerializer

    def get_queryset(self):
        return Order.objects.all()

    def get_permissions(self):
        if self.action in ['start_order', 'order_canceled', 'get_my_orders']:
            return [IsAuthenticated()]
        elif self.action in ['order_collecting', 'order_collected', 'order_shipped']:
            return [IsAuthenticated(), IsInGroups(['manager_base', 'employee_base'])]
        elif self.action in ['order_canceled', ]:
            return [IsAuthenticated(), IsInGroups(['manager_base', ])]
        else:
            return [IsAuthenticated(), IsInGroups(['manager_base'])]

    def __get_order_and_change_state(self, pk, state):
        try:
            order_obj = Order.objects.get(pk=pk)
        except Order.DoesNotExist:
            raise NotFound('Указанный заказ не найден.')

        order_obj.state = f'{state}'
        order_obj.save()

        return Response({
            'status': 'success',
            'message': f'Статус успешно обновлен на "{state}"'
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def get_my_orders(self, request):
        orders = Order.objects.filter(user=request.user).exclude(state='basket')

        if not orders.exists():
            return Response({
                'status': 'error',
                'message': 'У Вас нет заказов.'
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(orders, many=True)

        return Response({
            'status': 'success',
            'data': serializer.data,
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['patch'])
    def start_order(self, request, pk):
        try:
            order_obj = Order.objects.get(pk=pk)
        except Order.DoesNotExist:
            raise NotFound('Корзина с данным ID не найдена.')

        address_id = int(request.data.get('address'))

        if not address_id:
            return Response({
                'status': 'error',
                'message': 'В запросе не указан адрес.'
            })

        try:
            address_obj = Address.objects.get(id=address_id)
        except Address.DoesNotExist:
            raise NotFound('Указанный адрес не найден')

        if address_obj.user != self.request.user:
            return Response({
                'status': 'error',
                'message': 'Необходим адрес владельца заказа!'
            })

        try:
            with transaction.atomic():
                for item in order_obj.order_item.all():
                    product = Item.objects.get(pk=item.item.pk)
                    if product.quantity < item.quantity:
                        raise ValidationError(f'Недостаточно товара "{product.name}" на складе.')

                    product.decrease_quantity(item.quantity)
                    product.save(update_fields=['quantity'])

        except ValidationError as e:
            return Response({'status': 'error', 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        order_obj.address, order_obj.state = address_obj, 'created'
        order_obj.save()

        send_customer_order_confirmation(order_obj)
        generate_and_send_invoice_pdf(order_obj)

        return Response({
            'status': 'success',
            'message': 'Заказ успешно создан',
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['patch'])
    def order_collecting(self, request, pk):
        return __get_order_and_change_state(pk, 'collecting')

    @action(detail=True, methods=['patch'])
    def order_collected(self, request, pk):
        return __get_order_and_change_state(pk, 'collected')

    @action(detail=True, methods=['patch'])
    def order_shipped(self, request, pk):
        return __get_order_and_change_state(pk, 'shipped')

    @action(detail=True, methods=['patch'])
    def order_delivered(self, request, pk):
        try:
            order_obj = Order.objects.get(pk=pk)
        except Order.DoesNotExist:
            raise NotFound('Указанный заказ не найден')

        order_obj.state, order_obj.closed_at = 'delivered', datetime.datetime.now()
        order_obj.save()

        send_order_delivered_email(order_obj)

        return Response({
            'status': 'success',
            'message': 'Статус заказа изменен на "delivered".'
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['patch'])
    def order_canceled(self, request, pk):
        try:
            order_obj = Order.objects.get(pk=pk)
        except Order.DoesNotExist:
            raise NotFound('Указанный заказ не найден')

        comment = request.data.get('comment')
        if not comment:
            comment = 'Комментарий причины отказа отсутствует.'

        with transaction.atomic():
            for item in order_obj.order_item.all():
                product = Item.objects.get(pk=item.item.pk)

                product.quantity += item.quantity
                product.save(update_fields=['quantity'])

        order_obj.state, order_obj.comment, order_obj.closed_at = 'canceled', comment, datetime.datetime.now()
        order_obj.save()

        return Response({
            'status': 'success',
            'message': 'Заказ отменен.'
        }, status=status.HTTP_200_OK)


class UploadItemsCSV(APIView):
    parser_classes = [MultiPartParser]

    permission_classes = [IsAuthenticated, IsVendorOrManager]

    def post(self, request, *args, **kwargs):
        file = request.FILES.get('file')

        if not file or not file.name.endswith('.csv'):
            return Response({'error': 'Пожалуйста, загрузите CSV-файл.'}, status=status.HTTP_400_BAD_REQUEST)

        decoded_file = file.read().decode('utf-8')
        csv_reader = csv.DictReader(decoded_file.splitlines(), delimiter=';')

        items_to_create = []
        errors = []

        if request.user.groups.filter(name__in='manager_base').exists():
            vendor = request.data.get('vendor')
            if not vendor:
                return Response({
                    'status': 'error',
                    'message': 'В запросе не указан поставщик.'
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            vendor = request.user.id

        for row in csv_reader:
            print(row)

            row['vendor'] = vendor
            serializer = ItemSerializer(data=row)
            if serializer.is_valid():
                items_to_create.append(serializer.validated_data)
            else:
                errors.append(serializer.errors)

        if errors:
            return Response({
                'status': 'partial_success',
                'created': len(items_to_create),
                'errors': errors
            }, status=status.HTTP_207_MULTI_STATUS)

        items = [Item(**item) for item in items_to_create]
        Item.objects.bulk_create(items)

        return Response({
            'status': 'success',
            'message': f'Успешно создано {len(items_to_create)} товаров.'},
            status=status.HTTP_201_CREATED)
