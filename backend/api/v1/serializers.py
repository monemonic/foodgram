import base64

from django.contrib.auth.password_validation import validate_password
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.relations import SlugRelatedField
from rest_framework.validators import UniqueValidator

from .utils import create_ingredients_in_recipe
from foodgram.models import (
    Ingredient,
    Tag,
    Recipe,
    RecipeIngredient,
    Favorite,
    ShortLink,
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
        fields = [
            "avatar",
        ]


class SetPasswordSerializer(serializers.ModelSerializer):
    new_password = serializers.CharField(max_length=128)
    current_password = serializers.CharField(max_length=128)

    class Meta:
        model = User
        fields = ["new_password", "current_password"]

    def validate_new_password(self, value):
        validate_password(value)
        return value


class SafeMethodUserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField(read_only=True)

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
        ]

    def get_is_subscribed(self, obj):
        user = self.context.get("request")
        if user is None or user.user.is_anonymous:
            return False
        return Subscriptions.objects.filter(
            user=user.user, following=obj).exists()


class UserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=True,
        max_length=254,
        validators=[
            UniqueValidator(
                queryset=User.objects.all(),
                message="Этот email занят.")
        ],
    )
    username = serializers.RegexField(
        required=True,
        max_length=150,
        regex=r"^[\w.@+-]+$",
        validators=[
            UniqueValidator(
                queryset=User.objects.all(),
                message="username используется."
            )
        ],
    )
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            "id", "email", "username",
            "first_name", "last_name", "password"
        ]

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def to_representation(self, instance):
        if self.context["request"].method == "POST":
            return super().to_representation(instance)

        serializer = SafeMethodUserSerializer(
            instance, context={"request": self.context.get("request")}
        )
        return serializer.data


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

    def validate_amount(self, value):
        if value:
            return value
        raise serializers.ValidationError(
            "В обязательном поле amount значение должно быть больше 0."
        )


class RecipeSafeMethodSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    ingredients = IngredientInRecipeSerializer(many=True, source='recipes')
    author = SafeMethodUserSerializer()
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
        if user.is_anonymous:
            return False
        return Favorite.objects.filter(user=user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get("request").user
        if user.is_anonymous:
            return False
        return ShoppingCart.objects.filter(user=user, recipe=obj).exists()


class RecipeSerializer(serializers.ModelSerializer):
    ingredients = CreateRecipeIngredientSerializer(many=True, required=True)
    author = SlugRelatedField(slug_field="username", read_only=True)
    tags = serializers.SlugRelatedField(
        slug_field="id", queryset=Tag.objects.all(), many=True
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

    def validate_ingredients(self, value):
        print("asdasdasd")
        if not value:
            raise serializers.ValidationError(
                "В обязательном поле ingredients отсутствуют данные."
            )
        a = [a['ingredients'] for a in value]
        if len(a) != len(set(a)):
            raise serializers.ValidationError(
                "Нельза добавлять одинаковые ингредиенты."
            )
        return value

    def validate_tags(self, value):
        if not value:
            raise serializers.ValidationError(
                "В обязательном поле tags отсутствуют данные."
            )

        if len(value) != len(set(value)):
            raise serializers.ValidationError(
                "Нельза добавлять одинаковые теги."
            )
        return value

    def validate_cooking_time(self, value):
        if value:
            return value
        raise serializers.ValidationError(
            "В обязательном поле cooking_time значение должно быть больше 0."
        )

    def create(self, validated_data):
        ingredients = validated_data.pop("ingredients")
        tags = validated_data.pop("tags")
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)

        create_ingredients_in_recipe(ingredients, recipe)

        return recipe

    def update(self, instance, validated_data):
        self.validate_ingredients(validated_data.get('ingredients'))
        self.validate_tags(validated_data.get('tags'))
        ingredients = validated_data.pop("ingredients")
        tags = validated_data.pop("tags")
        recipe = get_object_or_404(Recipe, id=instance.id)
        recipe.tags.set(tags)
        instance.ingredients.clear()
        create_ingredients_in_recipe(ingredients, recipe)

        return super().update(instance, validated_data)

    def to_representation(self, instance):
        serializer = RecipeSafeMethodSerializer(
            instance, context={"request": self.context.get("request")}
        )
        return serializer.data


class RecipeSubscribeSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ("id", "name", "image", "cooking_time")
        model = Recipe


class SubscribeUserSerializer(SafeMethodUserSerializer):
    recipes = serializers.SerializerMethodField(read_only=True)
    recipes_count = serializers.SerializerMethodField(read_only=True)

    class Meta(SafeMethodUserSerializer.Meta):
        model = User
        fields = SafeMethodUserSerializer.Meta.fields + [
            "recipes", "recipes_count"
        ]

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_recipes(self, obj):
        if "recipes_limit" in self.context:
            recipes = obj.recipes.all().filter(author=obj)[
                : self.context["recipes_limit"]
            ]
        else:
            recipes = obj.recipes.all().filter(author=obj)
        serializer = RecipeSubscribeSerializer(
            recipes, many=True, read_only=True
        )
        return serializer.data


class ShortLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShortLink
        fields = ("short-link",)
        extra_kwargs = {
            "short-link": {"source": "short_url", "read_only": True},
        }
