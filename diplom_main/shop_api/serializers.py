from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, UserInfo, Position

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


class UserInfoSerializer(serializers.Serializer):

    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    type_info = serializers.CharField()
    value_info = serializers.CharField()

    class Meta:
        model = UserInfo
        fields = '__all__'

    def create(self, validated_data):
        return UserInfo.objects.create(**validated_data)

class PositionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Position
        fields = '__all__'