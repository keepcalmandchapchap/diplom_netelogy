from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from shop_api.serializers import RegisterSerializer

User = get_user_model()

user_1 = {
    'first_name': 'Павел',
    'last_name': 'Тестов',
    'email': 'test_clinet@diplom.com',
    'password': 'qwe',
}
user_2 = {
    'first_name': 'Дмитрий',
    'last_name': 'Иванов',
    'email': 'test_employee@diplom.com',
    'password': 'qwe',
}

user_3 = {
    'first_name': 'Анна',
    'last_name': 'Смирнова',
    'email': 'test_manager@diplom.com',
    'password': 'qwe'
}

user_4 = {
    'first_name': 'Игорь',
    'last_name': 'Брагин',
    'email': 'test_vendor@diplom.com',
    'password': 'qwe',
}

users = [user_1, user_2, user_3, user_4]


class Command(BaseCommand):
    help = 'Скрипт для создания 3-ех пользователей для тестов'

    def handle(self, *args, **options):
        for user_raw in users:
            if User.objects.filter(email=user_raw['email']).exists():
                self.stdout.write(self.style.WARNING(f'Пользователь с почтой "{user_raw['email']}" уже создан'))
                continue
            serializer = RegisterSerializer(data=user_raw)
            if serializer.is_valid():
                serializer.save()
                self.stdout.write(self.style.SUCCESS(f'Пользователь с почтой "{user_raw['email']}" успешно создан'))
            else:
                self.stdout.write(self.style.WARNING(f'Не получилось создаьб пользователя с почтой {user_raw['email']}'))
