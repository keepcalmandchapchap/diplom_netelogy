import os

from django.core.management import call_command
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Скрипт запуска команд для начальной работы с АПИ'

    def handle(self, *args, **options):
        commands = ['example_users', 'create_groups', 'user_to_group',]

        for command in commands:
            try:
                call_command(command)
                self.stdout.write(self.style.SUCCESS(f'Команда {command} применилась!'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Команда {command} не смогла примениться.'))