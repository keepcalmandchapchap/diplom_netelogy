# ✅ Действия для старта DRF-проекта

## 1. Подготовка окружения

### Установите зависимости:
sudo apt update

sudo apt install python3-pip python3-venv nginx postgresql postgresql-contrib \
    build-essential python3-dev git curl unzip weasyprint \

## 2. Настройка PostgreSQL

### Переключитесь на пользователя PostgreSQL:
sudo -u postgres psql

### Заменить пароль для УЗ БД.
ALTER USER postgres WITH PASSWORD 'password';

### Создайте БД и пользователя:
CREATE DATABASE diplom_db; \
\q \
exit

---

## 3. Склонируйте проект

В данном проекте предпологалось сохранить корневую папку проекта в директории opt/
git clone https://github.com/keepcalmandchapchap/diplom_netelogy/

---

## 4. Создайте и активируйте виртуальное окружение через venv

Выполнить команду: python3 -m venv .venv
Активироват виртуальную среду: source .venv/bin/actvate
Установить все необходимые модули: pip install -r diplom_main/requirements

---

## 5. Настройте `settings.py` и '.env'

### Обновите настройки базы данных:
DB_NAME=diplom_db \
DB_USER=postgres \
DB_PASSWORD='password' \
DB_HOST=localhost 

EMAIL_HOST=smtp.mail.ru \
EMAIL_PORT=2525 \
EMAIL_HOST_USER=... (почта для авторизации на smtp сервере) \
EMAIL_HOST_PASSWORD=... \
DEFAULT_FROM_EMAIL=... (почта для отправки писем по умолчанию) \
ORDER_NOTIFICATION_EMAIL=... (почта для отправки документов по заказам)

### Убедитесь, что установлены:
INSTALLED_APPS += ['rest_framework', 'diplom_main']

### Настройте:
ALLOWED_HOSTS = ['your_domain_or_ip'] \
DEBUG = False

STATIC_URL = '/static/' \
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

---

## 6. Выполните миграции и соберите статику

python manage.py makemigrations \
python manage.py migrate \
python manage.py collectstatic

---

## 7. Настройка Gunicorn как службы systemd

### Создайте юнит-файл:
sudo nano /etc/systemd/system/gunicorn.service

### Вставьте следующее (адаптируй под свой путь):
[Unit]
Description=Gunicorn for DRF project \
After=network.target

[Service]
User=root \
Group=www-data \
WorkingDirectory=/opt/diplom_netelogy \
ExecStart=/opt/diplom_netelogy/.venv/bin/gunicorn \
          --workers 3 \
          --bind unix:/run/gunicorn.sock \
          diplom_main.wsgi:application

[Install]
WantedBy=multi-user.target

### Активируйте службу:
sudo systemctl daemon-reload
sudo systemctl enable gunicorn
sudo systemctl start gunicorn

Проверь статус:
sudo systemctl status gunicorn

---

## 8. Настройка Nginx

### Создайте конфиг:
sudo nano /etc/nginx/sites-available/diplom_main

server {
    listen 80;
    server_name ip;

    location = /favicon.ico { access_log off; log_not_found off; }

    location /static/ {
        alias /opt/diplom_netelogy/diplom_main/staticfiles;
    }

    location / {
        proxy_pass http://unix:/run/gunicorn.sock:/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_read_timeout 120s;
    }
}

### Активируйте сайт:
sudo ln -s /etc/nginx/sites-available/diplom_main /etc/nginx/sites-enabled/

### Проверьте конфигурацию и перезапустите Nginx:
sudo nginx -t
sudo systemctl restart nginx

---


## ✅ Готово!

Теперь ваш DRF-проект доступен по адресу:
http://your_domain_or_ip

Если всё сделано верно, вы увидите Browsable API или ответ от вашего API.
