from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    first_name = models.CharField(
        "Имя", max_length=128,
        help_text="Имя пользователя, не более 128 символов"
    )
    last_name = models.CharField(
        "Фамилия",
        max_length=128,
        help_text="Фамилия пользователя, не более 128 символов",
    )
    avatar = models.ImageField(
        "Аватар",
        upload_to="foodgram/avatar/",
        null=True,
        default=None
    )

    class Meta:
        verbose_name = "пользователь"
        verbose_name_plural = "пользователи"
        ordering = ["id"]

    def __str__(self):
        return self.username


class Subscriptions(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="follower_subscribe"
    )
    following = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="following"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "following"], name="user_name_follow"
            ),
            models.CheckConstraint(
                name="user_prevent_self_follow",
                check=~models.Q(user=models.F("following")),
            ),
        ]
