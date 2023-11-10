from django.contrib import admin
from django.utils.safestring import mark_safe

from .models import (
    Favourite,
    Ingredient,
    Recipe,
    RecipeIngredients,
    ShoppingCartList,
    Tag,
)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Админка ингредиентов."""

    list_display = ("name", "measurement_unit")
    list_filter = ("name",)
    search_fields = ("name",)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Админка тэгов."""

    list_display = ("name", "color", "slug")
    list_editable = ("color", "slug")
    list_display_links = ("name",)
    search_fields = ("name", "slug")
    empty_value_display = "-пусто-"


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Админка рецетов."""

    list_display = (
        "name",
        "cooking_time",
        "text",
        "author",
        "ingredients_list",
        "favorites_count",
        "image"
    )
    list_editable = (
        "cooking_time",
        "text",
        "image",
        "author",
    )
    list_display_links = ("name",)
    list_filter = ("name",)
    search_fields = ("name", "author")
    empty_value_display = "-пусто-"

    def ingredients_list(self, obj):
        return ", ".join((str(ingredient) for ingredient
                          in obj.ingredients.all()))
    ingredients_list.short_description = "Ингредиенты"

    def favorites_count(self, obj):
        return obj.favourites_recipe.count()
    favorites_count.short_description = "Количество избранных рецептов"

    def image(self, obj):
        return mark_safe(f'<img src={obj.image.url} width="80" height="60">')
    image.short_description = "Изображение"


@admin.register(RecipeIngredients)
class RecipeIngredientsAdmin(admin.ModelAdmin):
    """Админка тэгов."""

    list_display = ("recipe", "ingredient", "amount")
    search_fields = ("recipe",)
    empty_value_display = "-пусто-"


@admin.register(ShoppingCartList)
class ShoppingCartListAdmin(admin.ModelAdmin):
    """Админка тэгов."""

    list_display = (
        "user",
        "recipe",
    )
    search_fields = ("recipe",)
    empty_value_display = "-пусто-"


@admin.register(Favourite)
class FavouriteAdmin(admin.ModelAdmin):
    """Админка тэгов."""

    list_display = (
        "user",
        "recipe",
    )
    search_fields = ("recipe", "user")
    empty_value_display = "-пусто-"
