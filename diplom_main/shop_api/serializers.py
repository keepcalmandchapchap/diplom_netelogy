from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, UserInfo, Position, StaffInfo, Address, VendorInfo, Item, Category, Order


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'


class RegisterSerializer(serializers.ModelSerializer):
    '''
    Сериализатор для регистрации
    '''
    password = serializers.CharField(write_only=True)

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


class ItemSerializer(serializers.ModelSerializer):
    categories = CategorySerializerForItem(many=True, read_only=True)

    class Meta:
        model = Item
        fields = ['id', 'name', 'vendor', 'price', 'updated_at', 'is_active', 'categories', 'quantity', ]
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
