from django.contrib import admin

from .models import (
    RecipeIngredient,
    Ingredient, Recipe,
    Tag,
    Favorite,
    ShoppingCart
)


class FavoriteInline(admin.StackedInline):
    model = Favorite
    extra = 1


class IngredientsInRecipeInline(admin.StackedInline):
    model = RecipeIngredient
    extra = 1
    min_num = 1


class ShoppingCartInline(admin.StackedInline):
    model = ShoppingCart
    extra = 1


class IngredientInRecipeAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "measurement_unit",
        "amount",
    )
    list_filter = ("amount", "name")
    search_fields = ("name",)
    filter_horizontal = ("ingredients",)


class RecipeAdmin(admin.ModelAdmin):
    inlines = (
        IngredientsInRecipeInline,
        ShoppingCartInline,
        FavoriteInline,
    )
    list_display = (
        "id",
        "name",
        "author",
        "text",
    )
    list_editable = ()
    search_fields = ("author", "name")
    list_filter = ("name",)
    list_display_links = ("name",)
    filter_horizontal = ("tags",)


admin.site.register(Tag)
admin.site.register(Ingredient)
admin.site.register(Favorite)
admin.site.register(ShoppingCart)
admin.site.register(Recipe, RecipeAdmin)
