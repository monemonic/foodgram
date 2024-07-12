from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django.http import FileResponse
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import (
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response

from .filters import RecipeFilters
from .permissions import IsAuthorOrReadOnly
from .serializers import (
    IngredientSerializer,
    PutAvatarSerializer,
    RecipeFavoriteSerializer,
    RecipeSerializer,
    SubscribeUserSerializer,
    ShoppingCartSerializer,
    TagSerializer,
    UserSerializer,
    SubscribeUserSafeMethodSerializer
)
from .utils import create_shopping_cart_pdf
from foodgram.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
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

    @action(detail=True, methods=["POST"])
    def favorite(self, request, pk):
        """Получение и удаление на рецепт."""
        recipe = get_object_or_404(Recipe, pk=pk).pk
        try:
            serializer = RecipeFavoriteSerializer(data={"recipe": recipe})
            serializer.is_valid(raise_exception=True)
            serializer.save(user=self.request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception:
            return Response(
                "Ошибка добавления в избранное",
                status=status.HTTP_400_BAD_REQUEST
            )

    @favorite.mapping.delete
    def delete_favorite(self, request, pk):
        user = self.request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        delete_favorite = Favorite.objects.filter(
            user=user, recipe=recipe).delete()

        if delete_favorite[0] == 0:
            return Response(
                "Вы не подписаны на этот рецепт.",
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            "Рецепт успешно удален из избранного",
            status=status.HTTP_204_NO_CONTENT
        )

    @action(detail=True, methods=["GET"], url_path="get-link")
    def get_link(self, request, pk):
        """Получение короткой ссылки на рецепт."""
        recipe_link = get_object_or_404(Recipe, pk=pk).short_url
        short_link = self.request.build_absolute_uri(recipe_link)
        return Response(
            ({"short-link": short_link}), status=status.HTTP_200_OK
        )

    @action(detail=True, methods=["POST"])
    def shopping_cart(self, request, pk):
        """Добавление и удаление рецептов из списка покупок."""
        recipe = get_object_or_404(Recipe, pk=pk).pk

        try:
            serializer = ShoppingCartSerializer(data=({"recipe": recipe}))
            serializer.is_valid(raise_exception=True)
            serializer.save(user=self.request.user)

            return Response(
                serializer.data, status=status.HTTP_201_CREATED
            )
        except Exception:
            return Response(
                "Ошибка добавления в список покупок",
                status=status.HTTP_400_BAD_REQUEST,
            )

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk):
        user = self.request.user
        recipe = get_object_or_404(Recipe, pk=pk)
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

        sc_ingredients = (
            RecipeIngredient.objects
            .filter(recipe__shopping_carts__user=self.request.user)
            .values('ingredients')
            .annotate(
                total_amount=Sum("amount")
            )
            .values_list(
                'ingredients', "ingredients__name",
                "ingredients__measurement_unit", "total_amount"
            )
        )

        shopping_cart = create_shopping_cart_pdf(sc_ingredients)

        return FileResponse(
            shopping_cart, as_attachment=True,
            filename=f"shopping cart {self.request.user}.pdf"
        )


class UsersViewSet(UserViewSet):

    """API для юзеров."""

    queryset = User.objects.all()
    pagination_class = LimitOffsetPagination
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)

    def destroy(self, request, *args, **kwargs):
        raise MethodNotAllowed(request.method)

    def update(self, request, *args, **kwargs):
        raise MethodNotAllowed(request.method)

    @action(
        detail=False, methods=["GET"],
        permission_classes=(IsAuthenticated,)
    )
    def me(self, request):
        """Получение страницы профиля текущего пользователя."""
        return super().me(request)

    @action(detail=True, methods=["POST"])
    def subscribe(self, request, **kwargs):
        """
        Создание и удаление подписки на пользователя текущим пользователем.
        """
        following = get_object_or_404(User, pk=self.kwargs['id']).pk

        try:
            serializer = SubscribeUserSerializer(
                data={"following": following},
                context={"request": request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save(user=self.request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception:
            return Response(
                "Ошибка подписки", status=status.HTTP_400_BAD_REQUEST
            )

    @subscribe.mapping.delete
    def delete_subscribe(self, request, **kwargs):
        user = self.request.user
        following = get_object_or_404(User, pk=self.kwargs['id'])

        delete_subscribe = Subscriptions.objects.filter(
            user=user, following=following
        ).delete()
        if delete_subscribe[0] == 0:
            return Response(
                "Вы не подписаны на этого пользователя.",
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response("Успешная отписка", status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False, methods=["GET"],
        permission_classes=(IsAuthenticated,)
    )
    def subscriptions(self, request):
        """Список подписок текущего пользователя."""
        queryset = User.objects.filter(following__user=self.request.user)
        page = self.paginate_queryset(queryset)

        serializer = SubscribeUserSafeMethodSerializer(
            page, many=True,
            context={"request": request}
        )
        return self.get_paginated_response(serializer.data)

    @action(detail=False, methods=["PUT"], url_path="me/avatar")
    def avatar(self, request):
        """Создание и удаление аватара текущего пользователя."""
        user = self.request.user
        serializer = PutAvatarSerializer(user, data=request.data)
        serializer.is_valid(raise_exception=True)
        user.avatar = serializer.validated_data.get("avatar")
        user.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @avatar.mapping.delete
    def delete_avatar(self, request, **kwargs):
        self.request.user.avatar.delete()
        return Response(
            "Аватар успешно удален", status=status.HTTP_204_NO_CONTENT
        )
