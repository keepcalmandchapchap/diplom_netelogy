from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.html import strip_tags
from django.utils.encoding import force_bytes
from django.contrib.auth.password_validation import validate_password
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from .models import User, UserInfo, Position, StaffInfo, Address, VendorInfo, Item, Category, Order, ItemInfo


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'


class PasswordResetSerializer(serializers.Serializer):
    email = serializers.CharField()

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Пользователь с таким email не найден.")
        return value

    def save(self, **kwargs):
        request = self.context.get('request')
        email = self.validated_data['email']
        user = User.objects.get(email=email)

        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))  # перврашщаем первичный ключ юзера в набор байтов и меняем символы непригодные для url

        reset_link = request.build_absolute_uri(
            f'/pass_reset_email/{uid}/{token}/')

        subject = 'Сброс пароля'
        html_message = render_to_string('emails/pass_reset_email.html', {
            'user': user,
            'reset_link': reset_link})

        plain_message = strip_tags(html_message)
        from_email = settings.DEFAULT_FROM_EMAIL
        to_email = [email]

        send_mail(
            subject, plain_message, from_email, to_email,
            html_message=html_message, fail_silently=False)


class PasswordResetConfirmSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                'new_password_confirm': 'Пароли не совпадают.'
            })
        return attrs


class RegisterSerializer(serializers.ModelSerializer):
    '''
    Сериализатор для регистрации
    '''
    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'date_joined', 'password']

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class LoginSerializer(serializers.Serializer):
    '''
    Сериализатор для входа
    '''
    email = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'password']

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = authenticate(request=self.context.get('request'), email=email, password=password)
            if not user:
                msg = 'Неверные учетные данные'
                raise serializers.ValidationError(msg, code='authorization')
        else:
            msg = 'Необходимо указать email и пароль'
            raise serializers.ValidationError(msg, code='authorization')
        attrs['user'] = user
        return attrs


class UserInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserInfo
        fields = '__all__'
        extra_kwargs = {
            'user': {'read_only': True},
        }


class PositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Position
        fields = '__all__'


class StaffInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = StaffInfo
        fields = '__all__'


class AddressClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = '__all__'
        extra_kwargs = {
            'user': {'read_only': True}
        }


class AddressManagerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = '__all__'


class VendorInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = VendorInfo
        fields = '__all__'


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


class CategorySerializerForItem(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']
        extra_kwargs = {
            'id': {'read_only': True},
            'name': {'read_only': True},
        }


class ItemInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemInfo
        fields = ['type_info', 'value_info']


class ItemSerializer(serializers.ModelSerializer):
    categories = CategorySerializerForItem(many=True, read_only=True)

    info = ItemInfoSerializer(many=True, write_only=True, required=False)

    class Meta:
        model = Item
        fields = ['id', 'name', 'vendor', 'price', 'updated_at', 'is_active', 'categories', 'quantity', 'info']
        extra_kwargs = {
            'id': {'read_only': True},
        }


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['user', 'address', 'state', 'comment', 'total_price', 'created_at', 'updated_at', 'closed_at']
        extra_kwargs = {
            'id': {'read_only': True, },
            'created_at': {'read_only': True, },
            'updated_at': {'read_only': True, },
        }
