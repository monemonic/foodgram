from django_filters.rest_framework import FilterSet, filters

from foodgram.models import Recipe


class RecipeFilters(FilterSet):
    is_favorited = filters.BooleanFilter(method="filter_is_favorited")
    is_in_shopping_cart = filters.BooleanFilter(
        method="filter_is_in_shopping_cart"
    )
    tags = filters.AllValuesMultipleFilter(
        field_name="tags__slug", lookup_expr="exact"
    )

    class Meta:
        model = Recipe
        fields = ["author", "tags"]

    def filter_is_favorited(self, qs, name, value):
        user = self.request.user
        if value and user.is_authenticated:
            return qs.filter(favorites__user=user)
        return qs

    def filter_is_in_shopping_cart(self, qs, name, value):
        user = self.request.user
        if value and user.is_authenticated:
            return qs.filter(shopping_carts__user=user)
        return qs
