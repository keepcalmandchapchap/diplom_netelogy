from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group

GROUPS = ['manager_base', 'employee_base', 'vendor_base', ]


class Command(BaseCommand):
    help = 'Команда для создания двух базовых групп - manager_base и employee_base'

    def handle(self, *args, **kwargs):
        for group_name in GROUPS:
            group, created = Group.objects.get_or_create(name=group_name)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Группа "{group_name}" успешно создана'))
            else:
                self.stdout.write(self.style.WARNING(f'Группа "{group_name}" уже существует'))
