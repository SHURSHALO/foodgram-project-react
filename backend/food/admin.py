from django.contrib import admin

from food.models import (
    Favorite,
    Follow,
    Ingredient,
    Recipe,
    RecipeIngredient,
    Shopping,
    Tag,
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


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'cooking_time')
    list_editable = ('cooking_time',)
    search_fields = ('name', 'author__username')
    list_filter = ('name', 'author', 'tags')
    list_display_links = ('name', 'author')
    inlines = [RecipeIngredientInline]


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'ingredients', 'amount')
    search_fields = ('recipe__name', 'ingredients__name')
    list_filter = ('recipe', 'ingredients')


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    search_fields = ('name', 'recipe__name', 'user__username')
    list_filter = ('user', 'recipe')


@admin.register(Shopping)
class ShoppingAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    search_fields = ('name', 'recipe__name', 'user__username')
    list_filter = ('user', 'recipe')


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('user', 'following')
    search_fields = ('user__username', 'following__username')
    list_filter = ('user', 'following')


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'cooking_time', 'total_favorites')

    def total_favorites(self, obj):
        return obj.favorite_count()

    total_favorites.short_description = 'Общее число добавлений в избранное'
