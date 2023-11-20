import django_filters
from food.models import Recipe, Tag


class RecipeFilter(django_filters.FilterSet):
    is_favorite = django_filters.BooleanFilter(
        field_name='favorite__user', method='filter_by_favorite'
    )
    author = django_filters.NumberFilter(field_name='author__id')
    is_in_shopping_cart = django_filters.BooleanFilter(
        field_name='shopping__user', method='filter_by_shopping_cart'
    )
    tags = django_filters.ModelMultipleChoiceFilter(
        field_name='tags__id', to_field_name='id', queryset=Tag.objects.all()
    )

    class Meta:
        model = Recipe
        fields = ['is_favorite', 'author', 'is_in_shopping_cart', 'tags']

    def filter_by_favorite(self, queryset, name, value):
        if value:
            return queryset.filter(favorite__user=self.request.user)
        return queryset

    def filter_by_shopping_cart(self, queryset, name, value):
        if value:
            return queryset.filter(shopping__user=self.request.user)
        return queryset
