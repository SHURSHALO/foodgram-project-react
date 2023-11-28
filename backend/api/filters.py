from django_filters import rest_framework
from rest_framework import filters
from food.models import Recipe
from users.models import User


class RecipeFilter(rest_framework.FilterSet):
    '''Кастомный фильтор для рецепта.'''

    author = rest_framework.ModelChoiceFilter(queryset=User.objects.all())
    tags = rest_framework.AllValuesMultipleFilter(field_name='tags__slug')
    is_favorited = rest_framework.BooleanFilter(method='get_is_favorited')
    is_in_shopping_cart = rest_framework.BooleanFilter(
        method='get_recipe_in_shopping_cart'
    )

    def get_is_favorited(self, queryset, name, value):
        if self.request.user.is_authenticated and value:
            return queryset.filter(favorite__user=self.request.user)
        return queryset

    def get_recipe_in_shopping_cart(self, queryset, name, value):
        if self.request.user.is_authenticated and value:
            return queryset.filter(shopping__user=self.request.user)
        return queryset

    class Meta:
        model = Recipe
        fields = (
            'author',
            'tags',
            'is_favorited',
            'is_in_shopping_cart',
        )


class CustomIngredientsSearchFilter(filters.SearchFilter):
    '''Кастомный фильтр для поиска ингредиента при создании рецепта.'''

    search_param = 'name'

    def get_search_fields(self, view, request):
        """Переопределение метода поиска полей."""
        if request.query_params.get('name'):
            return ['name']
        return super().get_search_fields(view, request)
