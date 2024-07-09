from django.contrib import admin

from .models import (
    RecipeTag, RecipeIngredient, Ingredient,
    Recipe, Tag
)


class TagInline(admin.StackedInline):
    model = RecipeTag
    extra = 0


class IngredientsInRecipeInline(admin.StackedInline):
    model = RecipeIngredient
    extra = 2


class IngredientInRecipeAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'measurement_unit',
        'amount',
    )
    list_filter = ('amount', 'name')
    search_fields = ('name',)


class RecipeAdmin(admin.ModelAdmin):
    inlines = (
        TagInline,
        IngredientsInRecipeInline,
    )
    list_display = (
        'id',
        'name',
        'author',
        'text',

    )
    list_editable = (

    )
    search_fields = ('author', 'name')
    list_filter = ('name',)
    list_display_links = ('name',)


admin.site.register(Tag)
admin.site.register(Ingredient)
admin.site.register(Recipe, RecipeAdmin)
