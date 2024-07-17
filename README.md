## Описание проекта.
Дипломный учебный проект. Проект представляет собой онлайн-сервис и API для него. На этом сервисе пользователи могут публиковать рецепты, подписываться на публикации других пользователей, добавлять понравившиеся рецепты в список «Избранное», а перед походом в магазин скачивать сводный список продуктов, необходимых для приготовления одного или нескольких выбранных блюд. Доступ к данным реализован через API-интерфейс. Документация к API написана с использованием Redoc.


## Стек технологий.

Python, Django, Django Rest Framework, ReportLab, Docker, Gunicorn, NGINX, PostgreSQL


## Особенности.
Проект завернут в Docker-контейнеры;
Образы foodgram_frontend, foodgram_gateway и foodgram_backend запушены на DockerHub;
Реализован workflow c автодеплоем на удаленный сервер и отправкой сообщения в Telegram;
URL-адресу сайта на котором находится проект: https://homeworkenkorolev.zapto.org


## Запуск проекта.

1. Клонировать репозиторий и перейти в него в командной строке:

```
git@github.com:monemonic/foodgram.git

```

2. Установить на сервере Docker, Docker Compose:

```
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh ./get-docker.sh

```

3. Для работы с GitHub Actions необходимо в репозитории в разделе Secrets > Actions создать переменные окружения:

```
DOCKER_PASSWORD         # пароль от Docker Hub
DOCKER_USERNAME         # логин Docker Hub
HOST                    # публичный IP сервера
SSH_KEY                 # приватный ssh-ключ
SSH_PASSPHRASE          # пароль от ssh-ключа
USER                    # имя пользователя на сервере
TELEGRAM_TO             # ID телеграм-аккаунта для посылки сообщения
TELEGRAM_TOKEN          # токен бота, посылающего сообщение
```

4. Отправить собранный проект на сервер с помощью github actions, триггером для запуска workflow служит git push в ветку main


5. При первом запуске проекте необходимо заполнить базу данных ингредиентами и тегами из подготовленных csv файлов:

```
sudo docker exec -it foodgram-backend-1 python manage.py csv_import ingredients
sudo docker exec -it foodgram-backend-1 python manage.py csv_import tags

```

6. Создать суперпользователя:

```
sudo docker exec -it foodgram-backend-1 python manage.py createsuperuser

```

## Примеры запросов и ответов на них:

1. POST запрос к /api/users/ формата:

```
{
  "email": "vpupkin@yandex.ru",
  "username": "vasya.pupkin",
  "first_name": "Вася",
  "last_name": "Иванов",
  "password": "Qwerty123"
}
```
Зарегистрирует пользователя и вернет ответ формата:

```
{
  "email": "vpupkin@yandex.ru",
  "id": 0,
  "username": "vasya.pupkin",
  "first_name": "Вася",
  "last_name": "Иванов"
}
```

При незаполнении одного или нескольких обязательных полей будет получена ошибка с ответом формата:

```
{
  "field_name": [
    "Обязательное поле."
  ]
}
```

2. GET запрос к /api/tags/ вернет список всех имеющихся тегов в формате:

```
[
  {
    "id": 0,
    "name": "Завтрак",
    "slug": "breakfast"
  }
]
```

3. GET запрос к /api/ingredients/{id}/ где id - уникальный идентификатор этого ингредиента вернет ответ с информацией о выбранном ингредиенте:

```
{
  "id": 0,
  "name": "Капуста",
  "measurement_unit": "кг"
}
```

## После каждого обновления репозитория (push в ветку master) будет происходить:
Сборка и доставка докер-образов frontend, gateway и backend на Docker Hub
Разворачивание проекта на удаленном сервере
Отправка сообщения в Telegram в случае успеха


Project Link: [https://github.com/monemonic/foodgram](https://github.com/monemonic/foodgram)