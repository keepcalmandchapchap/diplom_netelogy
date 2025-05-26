from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group


User = get_user_model()
# user_employee = User.objects.get(email='test_employee@diplom.com')
# user_manager = User.objects.get(email='test_manager@diplom.com')

# group_employee = Group.objects.get(name='employee_base')
# group_manager = Group.objects.get(name='manager_base')

# class Command(BaseCommand):
#     help = 'Команда для привязывания пользователей из примера к созданным группам'

#     def handle(self, *args, **options):
#         group_employee.set(user_employee)
#         self.stdout.write(self.style.SUCCESS(f'Пользователь {user_employee.email} привязан к группе "{group_employee.name}"'))
        
#         group_manager.set(user_manager)
#         self.stdout.write(self.style.SUCCESS(f'Пользователь {user_manager.email} привязан к группе "{group_manager.name}"'))

class Command(BaseCommand):
    help = 'Привязывает тестовых пользователей к группам'

    def handle(self, *arrgs, **kwargs):
        try:
            user_employee = User.objects.get(email='test_employee@diplom.com')
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR('Пользователь test_employee@diplom.com не найден'))

        try:
            user_manager = User.objects.get(email='test_manager@diplom.com')
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR('Пользователь test_manager@diplom.comm не найден'))


        try:   
            group_employee = Group.objects.get(name='employee_base')
        except Group.DoesNotExist:
            self.stdout.write(self.style.ERROR('Группа employee_base не найдена'))
        
        try:
            group_manager = Group.objects.get(name='manager_base')
        except Group.DoesNotExist:
            self.stdout.write(self.style.ERROR('Группа employee_base не найдена'))

        
        user_employee.groups.add(group_employee)
        user_employee.save()
        self.stdout.write(self.style.SUCCESS('Пользователь test_employee@diplom.com добавлен к группе employee_base'))

        user_manager.groups.add(group_manager)
        user_manager.save()
        self.stdout.write(self.style.SUCCESS('Пользователь test_manager@diplom.comm добавлен к группе manager_base'))