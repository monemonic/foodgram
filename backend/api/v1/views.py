from django.shortcuts import get_object_or_404
from django.http import FileResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .filters import RecipeFilters
from .permissions import IsAuthorOrReadOnly
from .serializers import (
    IngredientSerializer,
    PutAvatarSerializer,
    RecipeSerializer,
    RecipeSubscribeSerializer,
    SafeMethodUserSerializer,
    SetPasswordSerializer,
    ShortLinkSerializer,
    SubscribeUserSerializer,
    TagSerializer,
    UserSerializer,
)
from .utils import create_shopping_cart_pdf
from foodgram.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    ShortLink,
    Tag,
)
from users.models import User, Subscriptions


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """API для ингредиентов."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["name"]
    pagination_class = None


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """API для тегов."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """API для рецептов."""

    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = (IsAuthorOrReadOnly,)
    http_method_names = ["get", "post", "head", "patch", "delete"]
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilters

    def get_user(self):
        """Получение текущего пользователя."""
        return get_object_or_404(User, username=self.request.user)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        detail=True,
        methods=["POST", "DELETE"],
    )
    def favorite(self, request, pk):
        """Получение и удаление на рецепт."""
        user = self.get_user()
        recipe = get_object_or_404(Recipe, pk=pk)

        if request.method == "POST":
            try:
                Favorite.objects.create(user=user, recipe=recipe)

                serializer = RecipeSubscribeSerializer(recipe)
                return Response(
                    serializer.data,
                    status=status.HTTP_201_CREATED
                )
            except Exception:
                return Response(
                    "Ошибка добавления в избранное",
                    status=status.HTTP_400_BAD_REQUEST
                )

        delete_favorite = Favorite.objects.filter(user=user, recipe=recipe)
        if not delete_favorite:
            return Response(
                "Вы не подписаны на этот рецепт.",
                status=status.HTTP_400_BAD_REQUEST
            )

        delete_favorite.delete()
        return Response(
            "Рецепт успешно удален из избранного",
            status=status.HTTP_204_NO_CONTENT
        )

    @action(detail=True, methods=["GET", "DELETE"], url_path="get-link")
    def get_link(self, request, pk):
        """Получение короткой ссылки на рецепт."""
        long_url = request.build_absolute_uri(f"/api/recipes/{pk}/")
        short_url = request.build_absolute_uri(f"/s/{pk}/")

        if not ShortLink.objects.all().filter(long_url=long_url):
            ShortLink.objects.create(long_url=long_url, short_url=short_url)

        serializer = ShortLinkSerializer(
            get_object_or_404(ShortLink, short_url=short_url)
        )

        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=True,
        methods=["POST", "DELETE"],
    )
    def shopping_cart(self, request, pk):
        """Добавление и удаление рецептов из списка покупок."""
        user = self.get_user()
        recipe = get_object_or_404(Recipe, pk=pk)

        if request.method == "POST":
            try:
                ShoppingCart.objects.create(user=user, recipe=recipe)

                serializer = RecipeSubscribeSerializer(recipe)
                return Response(
                    serializer.data, status=status.HTTP_201_CREATED
                )
            except Exception:
                return Response(
                    "Ошибка добавления в список покупок",
                    status=status.HTTP_400_BAD_REQUEST,
                )

        try:
            user = get_object_or_404(ShoppingCart, user=user, recipe=recipe)
            user.delete()
            return Response(
                "Рецепт успешно удален из списка покупок",
                status=status.HTTP_204_NO_CONTENT,
            )
        except Exception:
            return Response(
                "Ошибка удаления из списка покупок",
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(
        detail=False,
        methods=["GET"],
    )
    def download_shopping_cart(self, request):
        """Скачивание списка покупок."""
        user = self.get_user()
        recipes = ShoppingCart.objects.all().filter(user=user)

        sc_ingredients = {}

        for recipe in recipes:
            all_ingredients = RecipeIngredient.objects.all().filter(
                recipe=recipe.recipe
            )
            for ingredient in all_ingredients:
                ingr = ingredient.ingredients
                dict_key = f"{ingr.name} {ingr.measurement_unit}"
                if dict_key in sc_ingredients:
                    sc_ingredients[dict_key] = (
                        sc_ingredients[dict_key] + ingredient.amount
                    )
                    continue
                sc_ingredients[dict_key] = ingredient.amount

        shopping_cart = create_shopping_cart_pdf(sc_ingredients)

        return FileResponse(
            shopping_cart, as_attachment=True,
            filename=f"shopping cart {user}.pdf"
        )


class UsersViewSet(viewsets.ModelViewSet):
    """API для юзеров."""

    queryset = User.objects.all()
    pagination_class = LimitOffsetPagination
    serializer_class = UserSerializer

    def get_user(self):
        """Получение текущего пользователя."""
        return get_object_or_404(User, username=self.request.user)

    def destroy(self, request, *args, **kwargs):
        raise MethodNotAllowed(request.method)

    def update(self, request, *args, **kwargs):
        raise MethodNotAllowed(request.method)

    @action(detail=False, methods=["GET"])
    def me(self, request):
        """Получение страницы профиля текущего пользователя"""
        try:
            user = self.get_user()
            serializer = SafeMethodUserSerializer(user)
            return Response(serializer.data)
        except Exception:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

    @action(detail=False, methods=["POST"], url_path="set_password")
    def set_password(self, request):
        """Изменение пароля текущего пользователя."""
        user = self.get_user()
        serializer = SetPasswordSerializer(data=request.data)

        if serializer.is_valid():
            current_password = (
                serializer.validated_data.get("current_password")
            )
            if not user.check_password(current_password):
                return Response(
                    {"current_password": ["Неверный пароль."]},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            user.set_password(serializer.validated_data.get("new_password"))
            user.save()
            return Response(
                "Пароль успешно изменен",
                status=status.HTTP_204_NO_CONTENT
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=True, methods=["POST", "DELETE"],
        permission_classes=(IsAuthenticated,)
    )
    def subscribe(self, request, pk):
        """
        Создание и удаление подписки на пользователя текущим пользователем.
        """
        user = self.get_user()
        following = get_object_or_404(User, pk=pk)

        if request.method == "POST":
            try:
                Subscriptions.objects.create(user=user, following=following)
                serializer = SubscribeUserSerializer(following)
                url = request.build_absolute_uri()
                if "recipes_limit" in url:
                    limit = url.split("=")
                    serializer.context["recipes_limit"] = int(limit[1])

                return Response(
                    serializer.data, status=status.HTTP_201_CREATED
                )

            except Exception:
                return Response(
                    "Ошибка подписки", status=status.HTTP_400_BAD_REQUEST
                )

        delete_subscribe = Subscriptions.objects.filter(
            user=user, following=following
        )
        if not delete_subscribe:
            return Response(
                "Вы не подписаны на этого пользователя.",
                status=status.HTTP_400_BAD_REQUEST,
            )
        delete_subscribe.delete()
        return Response("Успешная отписка", status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False, methods=["GET"],
        permission_classes=(IsAuthenticated,)
    )
    def subscriptions(self, request):
        """Список подписок текущего пользователя."""
        user = self.get_user()
        queryset = User.objects.filter(following__user=user)
        url = request.build_absolute_uri()

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = SubscribeUserSerializer(page, many=True)
            if "recipes_limit" in url:
                limit = url.split("=")
                serializer.context["recipes_limit"] = int(limit[1])
            return self.get_paginated_response(serializer.data)

        serializer = SubscribeUserSerializer(queryset, many=True)
        if "recipes_limit" in url:
            limit = url.split("=")
            serializer.context["recipes_limit"] = int(limit[1])
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["PUT", "DELETE"], url_path="me/avatar")
    def avatar(self, request):
        """Создание и удаление аватара текущего пользователя."""
        if self.request.user.is_anonymous:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        user = self.get_user()
        if request.method == "PUT":
            if "avatar" not in request.data:
                return Response(
                    {"avatar": ["Обязательное поле."]},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            serializer = PutAvatarSerializer(user, data=request.data)
            if serializer.is_valid(raise_exception=True):
                user.avatar = serializer.validated_data.get("avatar")
                user.save()
                return Response(serializer.data, status=status.HTTP_200_OK)

        user.avatar.delete()
        return Response(
            "Аватар успешно удален", status=status.HTTP_204_NO_CONTENT
        )
