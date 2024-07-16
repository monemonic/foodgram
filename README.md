## Описание проекта.
Дипломный учебный проект. Проект представляет собой онлайн-сервис и API для него. На этом сервисе пользователи могут публиковать рецепты, подписываться на публикации других пользователей, добавлять понравившиеся рецепты в список «Избранное», а перед походом в магазин скачивать сводный список продуктов, необходимых для приготовления одного или нескольких выбранных блюд.
Проект реализован на Django и DjangoRestFramework. Доступ к данным реализован через API-интерфейс. Документация к API написана с использованием Redoc.


## Особенности.
Проект завернут в Docker-контейнеры;
Образы foodgram_frontend, foodgram_gateway и foodgram_backend запушены на DockerHub;
Реализован workflow c автодеплоем на удаленный сервер и отправкой сообщения в Telegram;
URL-адресу сайта на котором находится проект: https://homeworkenkorolev.zapto.org


## Запуск проекта

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
sudo docker compose exec backend python manage.py csv_import ingredients
sudo docker compose exec backend python manage.py csv_import tags

```

6. Создать суперпользователя:

```
sudo docker compose exec backend python manage.py createsuperuser

```

## После каждого обновления репозитория (push в ветку master) будет происходить:
Сборка и доставка докер-образов frontend, gateway и backend на Docker Hub
Разворачивание проекта на удаленном сервере
Отправка сообщения в Telegram в случае успеха


Project Link: [https://github.com/monemonic/foodgram](https://github.com/monemonic/foodgram)