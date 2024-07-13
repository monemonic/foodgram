from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.crypto import get_random_string

from users.models import User
from backend.constants import (
    INGREDIENT_NAME_FIELD_MAX_LENGTH,
    TAG_FIELD_MAX_LENGTH,
    RECIPE_FIELD_MAX_LENGTH,
    MIN_VALUE_VALIDATOR_COOKING_TIME,
    MAX_VALUE_VALIDATOR_COOKING_TIME,
    MIN_VALUE_VALIDATOR_AMOUNT,
    MAX_VALUE_VALIDATOR_AMOUNT,
    SHORT_URL_MAX_LENGTH,
    LENGTH_STRING_FOR_SHORT_LINK,
    MEANSUREMENT_UNIT_MAX_LENGTH,
)


class Ingredient(models.Model):
    name = models.CharField(
        "Название",
        max_length=INGREDIENT_NAME_FIELD_MAX_LENGTH,
        help_text=f"Название ингредиента, не более \
            {INGREDIENT_NAME_FIELD_MAX_LENGTH} символов",
    )
    measurement_unit = models.CharField(
        "Единица измерения",
        max_length=MEANSUREMENT_UNIT_MAX_LENGTH,
        help_text=f"Единица измерения, не более \
            {MEANSUREMENT_UNIT_MAX_LENGTH} символов",
    )

    class Meta:
        verbose_name = "Ингредиент"
        verbose_name_plural = "ингредиенты"
        ordering = ["name", "measurement_unit"]
        constraints = [
            models.UniqueConstraint(
                fields=("name", "measurement_unit"),
                name="unique_name_measurement_unit"
            )
        ]

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(
        "Название",
        max_length=TAG_FIELD_MAX_LENGTH,
        help_text=f"Имя тега, не более {TAG_FIELD_MAX_LENGTH} символов",
    )
    slug = models.SlugField(
        "Слаг",
        unique=True,
        max_length=TAG_FIELD_MAX_LENGTH,
        help_text=f"Слаг тега, не более {TAG_FIELD_MAX_LENGTH} символов",
    )

    class Meta:
        verbose_name = "Тег"
        verbose_name_plural = "теги"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Recipe(models.Model):
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name="Автор"
    )
    name = models.CharField(
        "Название",
        max_length=RECIPE_FIELD_MAX_LENGTH,
        help_text=f"Название блюда, не более \
            {RECIPE_FIELD_MAX_LENGTH} символов",
    )
    image = models.ImageField(
        upload_to="foodgram/recipe/",
        verbose_name="Изображение",
        help_text="Фотография блюда",
    )
    text = models.TextField("Описание", help_text="Описание блюда")
    ingredients = models.ManyToManyField(
        Ingredient,
        through="RecipeIngredient",
        through_fields=("recipe", "ingredients"),
        verbose_name="Ингредиент",
    )

    tags = models.ManyToManyField(
        Tag,
        verbose_name="Тег",
    )
    cooking_time = models.PositiveSmallIntegerField(
        "Время приговления",
        help_text="Время приготовления блюда, значение в минутах",
        validators=[
            MinValueValidator(
                MIN_VALUE_VALIDATOR_COOKING_TIME,
                message=f"Значение не может быть меньше, \
                    чем {MIN_VALUE_VALIDATOR_COOKING_TIME}",
            ),
            MaxValueValidator(
                MAX_VALUE_VALIDATOR_COOKING_TIME,
                message=f"Значение не может быть больше, \
                    чем {MAX_VALUE_VALIDATOR_COOKING_TIME}",
            ),
        ],
    )
    created_at = models.DateTimeField(auto_now_add=True)
    short_url = models.CharField(
        "Короткая ссылка", max_length=SHORT_URL_MAX_LENGTH
    )

    class Meta:
        ordering = ["-created_at"]
        default_related_name = "recipes"
        verbose_name = "Рецепт"
        verbose_name_plural = "рецепты"

    def __str__(self):
        return self.name

    def create_unique_short_link(self):
        unique_url = get_random_string(length=LENGTH_STRING_FOR_SHORT_LINK)

        if not Recipe.objects.filter(short_url=unique_url).exists():
            return unique_url
        else:
            self.create_unique_short_link()

    def save(self, *args, **kwargs):
        self.short_url = f"/{self.create_unique_short_link()}/"
        super().save(*args, **kwargs)


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="recipes",
        help_text="Для какого рецепта используется ингредиент.",
    )
    ingredients = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name="ingredients",
        help_text="Какой ингредиент используется для рецепта.",
    )
    amount = models.PositiveSmallIntegerField(
        "Количество",
        help_text="Количество ингредиента, в указанных единицах измерения",
        validators=[
            MinValueValidator(
                MIN_VALUE_VALIDATOR_AMOUNT,
                message=f"Значение не может быть меньше, \
                    чем {MIN_VALUE_VALIDATOR_AMOUNT}",
            ),
            MaxValueValidator(
                MAX_VALUE_VALIDATOR_AMOUNT,
                message=f"Значение не может быть больше, \
                    чем {MIN_VALUE_VALIDATOR_AMOUNT}",
            ),
        ],
    )

    class Meta:
        verbose_name = "Ингредиент в рецепте"
        verbose_name_plural = "ингредиенты в рецепте"
        constraints = [
            models.UniqueConstraint(
                fields=("recipe", "ingredients"),
                name="unique_recipe_ingredients"
            )
        ]

    def __str__(self):
        return f"{self.recipe} {self.ingredients}"


class DefaultRecipeAction(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Пользователь",
        help_text="Пользователь, который добавил рецепт.",
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name="Рецепт",
        help_text="Рецепт, добавленный пользователем.",
    )

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.user} {self.recipe}"


class Favorite(DefaultRecipeAction):
    class Meta:
        default_related_name = "favorites"
        verbose_name = "Избранный рецепт"
        verbose_name_plural = "Избранные рецепты"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"], name="user_recipe_favorite"
            ),
        ]


class ShoppingCart(DefaultRecipeAction):
    class Meta:
        default_related_name = "shopping_carts"
        verbose_name = "Список покупок"
        verbose_name_plural = "Списки покупок"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"], name="user_recipe_shopping_carts"
            ),
        ]
