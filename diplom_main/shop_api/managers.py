from django.contrib.auth.base_user import BaseUserManager


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, first_name, last_name, email, password, **extra_fields):
        '''
        Создает и сохраняет пользователя
        '''
        if not first_name:
            raise ValueError('Имя должно быть указано')
        if not last_name:
            raise ValueError('Фамилия должна быть указана')
        if not email:
            raise ValueError('Электронная почта должна быть указана')
        email = self.normalize_email(email)
        user = self.model(first_name=first_name, last_name=last_name, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, first_name, last_name, email, password=None, **extra_fields):
        extra_fields.setdefault('is_active', False)
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(first_name, last_name, email, password, **extra_fields)

    def create_superuser(self, first_name, last_name, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self._create_user(first_name, last_name, email, password, **extra_fields)
