from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator

from backend.constants import (
    USER_NAME_FIELD_MAX_LENGTH,
    EMAIL_FIELD_MAX_LENGTH
)


class User(AbstractUser):
    first_name = models.CharField(
        "Имя", max_length=USER_NAME_FIELD_MAX_LENGTH,
        help_text=f"Имя пользователя, не более \
            {USER_NAME_FIELD_MAX_LENGTH} символов"
    )
    last_name = models.CharField(
        "Фамилия",
        max_length=USER_NAME_FIELD_MAX_LENGTH,
        help_text=f"Фамилия пользователя, не более \
            {USER_NAME_FIELD_MAX_LENGTH} символов",
    )
    avatar = models.ImageField(
        "Аватар",
        upload_to="foodgram/avatar/",
        null=True,
        default=None
    )
    email = models.EmailField(
        "Электронная почта", unique=True,
        max_length=EMAIL_FIELD_MAX_LENGTH,
        help_text="Электронная почта пользователя"
    )

    username = models.CharField(
        "Юзернейм",
        validators=[
            RegexValidator(
                regex=r"^[\w.@+-]+$",
                message="Юзернейм не подходит.",
            ),
        ],
        max_length=USER_NAME_FIELD_MAX_LENGTH,
        help_text=f"Юзернейм пользователя, не более \
            {USER_NAME_FIELD_MAX_LENGTH} символов",
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["last_name", "first_name", "username"]

    class Meta:
        verbose_name = "пользователь"
        verbose_name_plural = "пользователи"
        ordering = ["-date_joined", "username"]

    def __str__(self):
        return self.username


class Subscriptions(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name="follower_subscribe",
        verbose_name="Подписчик",
        help_text="Username пользователя, который подписан",
    )
    following = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="following",
        verbose_name="Подписка",
        help_text="Username пользователя, на которого подписка",
    )

    class Meta:
        verbose_name = "Подписка"
        verbose_name_plural = "подписки"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "following"], name="user_name_follow"
            ),
            models.CheckConstraint(
                name="user_prevent_self_follow",
                check=~models.Q(user=models.F("following")),
            ),
        ]

    def __str__(self):
        return f"{self.user} {self.following}"
