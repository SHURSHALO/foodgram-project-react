from django.contrib import admin
from .models import (
    Tag,
    Ingredient,
    Recipe,
    Favorite,
    RecipeIngredient,
    Follow,
    Shopping,
)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'slug')
    search_fields = ('name', 'slug')
    list_filter = ('name', 'color')


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('name',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'cooking_time')
    list_editable = ('cooking_time',)
    search_fields = ('name', 'author__username')
    list_filter = ('author', 'tags', 'ingredients')
    list_display_links = ('name', 'author')


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'ingredients', 'amount')
    search_fields = ('recipe__name', 'ingredients__name')
    list_filter = ('recipe', 'ingredients')


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'recipe', 'cooking_time')
    search_fields = ('name', 'recipe__name', 'user__username')
    list_filter = ('user', 'recipe')


@admin.register(Shopping)
class ShoppingAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'recipe', 'cooking_time')
    search_fields = ('name', 'recipe__name', 'user__username')
    list_filter = ('user', 'recipe')


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('user', 'following')
    search_fields = ('user__username', 'following__username')
    list_filter = ('user', 'following')
