import base64

from django.core.files.base import ContentFile
from rest_framework import serializers
from rest_framework.relations import SlugRelatedField
from rest_framework.validators import UniqueValidator

from foodgram.models import (
    Ingredient,
    Tag,
    Recipe,
    RecipeIngredient,
    Favorite,
    ShoppingCart,
)
from users.models import User, Subscriptions


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ("id", "name", "slug")
        lookup_field = "slug"
        model = Tag


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ("id", "name", "measurement_unit")
        model = Ingredient


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith("data:image"):
            format, imgstr = data.split(";base64,")
            ext = format.split("/")[-1]

            data = ContentFile(base64.b64decode(imgstr), name="temp." + ext)

        return super().to_internal_value(data)


class PutAvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ["avatar"]


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField(read_only=True)
    password = serializers.CharField(write_only=True)
    email = serializers.EmailField(
        required=True,
        max_length=254,
        validators=[
            UniqueValidator(
                queryset=User.objects.all(),
                message="Этот email занят.")
        ],
    )

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "avatar",
            "password"
        ]

    def get_is_subscribed(self, obj):
        user = (self.context.get("request"))
        return (
            user and not user.user.is_anonymous
            and Subscriptions.objects.filter(
                user=user.user, following=obj).exists()
        )


class IngredientInRecipeSerializer(serializers.ModelSerializer):

    id = serializers.ReadOnlyField(source='ingredients.id')
    name = serializers.ReadOnlyField(source='ingredients.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredients.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = (
            'id', 'name',
            'measurement_unit', 'amount'
        )


class CreateRecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(), source="ingredients"
    )

    class Meta:
        model = RecipeIngredient
        fields = ("id", "amount")


class RecipeSafeMethodSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    ingredients = IngredientInRecipeSerializer(many=True, source='recipes')
    author = UserSerializer()
    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)

    class Meta:
        fields = (
            "id",
            "tags",
            "author",
            "ingredients",
            "name",
            "image",
            "text",
            "cooking_time",
            "is_favorited",
            "is_in_shopping_cart",
        )
        model = Recipe

    def get_is_favorited(self, obj):
        user = self.context.get("request").user

        return (
            user and not user.is_anonymous
            and Favorite.objects.filter(user=user, recipe=obj).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get("request").user

        return (
            user and not user.is_anonymous
            and ShoppingCart.objects.filter(user=user, recipe=obj).exists()
        )


class RecipeSerializer(serializers.ModelSerializer):
    ingredients = CreateRecipeIngredientSerializer(many=True, required=True)
    author = SlugRelatedField(slug_field="username", read_only=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )
    image = Base64ImageField()

    class Meta:
        fields = (
            "author",
            "name",
            "image",
            "text",
            "ingredients",
            "tags",
            "cooking_time",
        )
        model = Recipe

    def validate(self, data):
        field = ("ingredients", "tags")
        for value in field:
            if value not in data or not data[value]:
                raise serializers.ValidationError(
                    {value:
                     f"В обязательном поле {value} отсутствуют данные."
                     }
                )
        values = {
            "ингредиенты": [a['ingredients'] for a in data["ingredients"]],
            "теги": data["tags"]
        }
        for key, value in values.items():
            if len(value) != len(set(value)):
                raise serializers.ValidationError(
                    {key: f"Нельза добавлять одинаковые {key}."}
                )
        return data

    def create_ingredients_in_recipe(self, ingredients, recipe):
        """Создание ингредиентов для рецепта."""
        RecipeIngredient.objects.bulk_create([
            RecipeIngredient(
                recipe=recipe,
                ingredients=ing["ingredients"],
                amount=ing["amount"]
            )for ing in ingredients])

    def create(self, validated_data):
        ingredients = validated_data.pop("ingredients")
        tags = validated_data.pop("tags")
        recipe = Recipe.objects.create(
            author=self.context['request'].user, **validated_data
        )
        recipe.tags.set(tags)

        self.create_ingredients_in_recipe(ingredients, recipe)

        return recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.pop("ingredients")
        tags = validated_data.pop("tags")
        instance.tags.set(tags)
        instance.ingredients.clear()
        create_ingredients_in_recipe(ingredients, instance)

        return super().update(instance, validated_data)

    def to_representation(self, instance):
        serializer = RecipeSafeMethodSerializer(
            instance, context={"request": self.context.get("request")}
        )
        return serializer.data


class RecipeFavoriteSafeMethodSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ("id", "name", "image", "cooking_time")
        model = Recipe


class RecipeFavoriteSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    recipe = serializers.PrimaryKeyRelatedField(
        queryset=Recipe.objects.all()
    )

    class Meta:
        fields = ("user", "recipe")
        model = Favorite

    def to_representation(self, instance):
        serializer = RecipeFavoriteSafeMethodSerializer(instance.recipe)
        return serializer.data


class SubscribeUserSafeMethodSerializer(UserSerializer):
    recipes = serializers.SerializerMethodField(read_only=True)
    recipes_count = serializers.SerializerMethodField(read_only=True)

    class Meta(UserSerializer.Meta):
        model = User
        fields = UserSerializer.Meta.fields + [
            "recipes", "recipes_count"
        ]

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_recipes(self, obj):
        count = self.context.get('request').GET.get('recipes_limit')
        recipes = obj.recipes.all()
        try:
            if count:
                recipes = recipes[:int(count)]
        except Exception:
            pass
        serializer = RecipeFavoriteSafeMethodSerializer(
            recipes, many=True, read_only=True
        )
        return serializer.data


class SubscribeUserSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    following = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all()
    )

    class Meta:
        fields = ("user", "following")
        model = Subscriptions

    def to_representation(self, instance):
        serializer = SubscribeUserSafeMethodSerializer(
            instance.following,
            context={"request": self.context.get("request")}
        )
        return serializer.data


class ShoppingCartSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    recipe = serializers.PrimaryKeyRelatedField(
        queryset=Recipe.objects.all()
    )

    class Meta:
        fields = ("user", "recipe")
        model = ShoppingCart

    def to_representation(self, instance):
        serializer = RecipeFavoriteSafeMethodSerializer(instance.recipe)
        return serializer.data
