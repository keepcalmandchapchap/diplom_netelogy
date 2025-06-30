from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group


User = get_user_model()

class Command(BaseCommand):
    help = 'Привязывает тестовых пользователей к группам'

    def handle(self, *arrgs, **kwargs):
        users = ['test_employee@diplom.com', 'test_manager@diplom.com', 'test_vendor@diplom.com', ]
        try:
            user_employee = User.objects.get(email='test_employee@diplom.com')
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR('Пользователь test_employee@diplom.com не найден'))

        try:
            user_manager = User.objects.get(email='test_manager@diplom.com')
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR('Пользователь test_manager@diplom.comm не найден'))

        try:
            user_vendor = User.objects.get(email='test_vendor@diplom.com')
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR('Пользователь test_vendor@diplom.com не найден'))


        try:   
            group_employee = Group.objects.get(name='employee_base')
        except Group.DoesNotExist:
            self.stdout.write(self.style.ERROR('Группа employee_base не найдена'))
        
        try:
            group_manager = Group.objects.get(name='manager_base')
        except Group.DoesNotExist:
            self.stdout.write(self.style.ERROR('Группа manager_base не найдена'))

        try:
            group_vendor = Group.objects.get(name='vendor_base')
        except Group.DoesNotExist:
            self.stdout.write(self.style.ERROR('Группа vendor_base не найдена'))

        
        user_employee.groups.add(group_employee)
        user_employee.save()
        self.stdout.write(self.style.SUCCESS('Пользователь test_employee@diplom.com добавлен к группе employee_base'))

        user_manager.groups.add(group_manager)
        user_manager.save()
        self.stdout.write(self.style.SUCCESS('Пользователь test_manager@diplom.comm добавлен к группе manager_base'))

        user_vendor.groups.add(group_vendor)
        user_vendor.save()
        self.stdout.write(self.style.SUCCESS('Пользователь test_vendor@diplom.com добавлен к группе vendor_base'))