from django.db import models
from django.core.validators import MinValueValidator

from users.models import User


class Ingredient(models.Model):
    name = models.CharField(
        "Название",
        max_length=128,
        help_text="Название ингредиента, не более 128 символов",
    )
    measurement_unit = models.CharField(
        "Единица измерения",
        max_length=64,
        help_text="Единица измерения, не более 64 символов",
    )

    class Meta:
        verbose_name = "Ингредиент"
        verbose_name_plural = "ингредиенты"
        ordering = ["id"]

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(
        "Название", max_length=32, help_text="Имя тега, не более 32 символов"
    )
    slug = models.SlugField(
        "Слаг", unique=True, max_length=32,
        help_text="Слаг тега, не более 32 символов"
    )

    class Meta:
        verbose_name = "Тег"
        verbose_name_plural = "теги"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Recipe(models.Model):
    author = models.ForeignKey(
        User, on_delete=models.CASCADE,
        verbose_name="Автор"
    )
    name = models.CharField(
        "Название", max_length=256,
        help_text="Название блюда, не более 256 символов"
    )
    image = models.ImageField(
        upload_to="foodgram/recipe/",
        verbose_name="Изображение",
        help_text="Фотография блюда",
    )
    text = models.TextField("Описание", help_text="Описание блюда")
    ingredients = models.ManyToManyField(
        Ingredient, through="RecipeIngredient",
        through_fields=("recipe", "ingredients"),
        verbose_name="Ингредиент"
    )

    tags = models.ManyToManyField(
        Tag,
        through="RecipeTag",
        verbose_name="Тег",
    )
    cooking_time = models.PositiveSmallIntegerField(
        "Время приговления",
        help_text="Время приготовления блюда, значение в минутах",
        validators=[MinValueValidator(1)]
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        default_related_name = "recipes"
        verbose_name = "Рецепт"
        verbose_name_plural = "рецепты"

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE,
        related_name="recipes",
        help_text="Для какого рецепта используется ингредиент."
    )
    ingredients = models.ForeignKey(
        Ingredient, on_delete=models.CASCADE,
        related_name='ingredients',
        help_text="Какой ингредиент используется для рецепта."
    )
    amount = models.PositiveSmallIntegerField(
        "Количество",
        validators=[MinValueValidator(1)],
        help_text="Количество ингредиента, в указанных единицах измерения"
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


class RecipeTag(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Тег рецепта"
        verbose_name_plural = "теги рецептa"
        constraints = [
            models.UniqueConstraint(
                fields=("recipe", "tag"), name="unique_recipe_tag")
        ]

    def __str__(self):
        return f"{self.recipe} {self.tag}"


class Favorite(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="follower_recipe"
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name="favorite"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"], name="user_follow_recipe"
            ),
        ]


class ShortLink(models.Model):
    long_url = models.URLField("URL", max_length=60, unique=True)
    short_url = models.URLField("shorts", max_length=60, unique=True)


class ShoppingCart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)

    class Meta:
        default_related_name = "shopping_carts"

        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"], name="user_recipe_shopping_cart"
            ),
        ]
