import os

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from django.db.models import F
from django.db.models import Sum
from rest_framework import (
    mixins,
    permissions,
    status,
    viewsets,
)
from rest_framework.decorators import action
from rest_framework.response import Response
from users.models import User

from food.models import (
    Favorite,
    Follow,
    Ingredient,
    Recipe,
    RecipeIngredient,
    Shopping,
    Tag,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from api.filters import (
    RecipeFilter,
    CustomIngredientsSearchFilter,
)
from api.permissions import IsAuthor
from api.serializers import (
    CreateUserSerializer,
    FavoriteSerializer,
    FavoriteShoppingSerializer,
    IngredientsSerializer,
    RecipeDetailSerializer,
    RecipeSerializer,
    ShoppingSerializer,
    SubscribeSerializer,
    TagsSerializer,
    UserGetSerializer,
)
from backend.settings import SHOPPING_CART_FILE_NAME


RESPONSE_CONTENT_TYPE = 'application/pdf'


class RetrieveListViewSet(
    mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet
):
    pass


class TagsViewSet(RetrieveListViewSet):
    '''Представление для тэг.'''

    queryset = Tag.objects.all()
    serializer_class = TagsSerializer
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    '''
    Представление для рецепта, избранное, корзина,
    PDF списка ингредиентов.
    '''

    queryset = Recipe.objects.annotate(created_at=F('id')).order_by(
        '-created_at'
    )
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter

    def get_permissions(self):
        if self.action == 'create':
            return (permissions.IsAuthenticated(),)
        elif self.action in ('update', 'destroy'):
            return (IsAuthor(),)
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeDetailSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        detail=True,
        methods=(
            'post',
            'delete',
        ),
        permission_classes=(permissions.IsAuthenticated,),
    )
    def favorite(self, request, pk=None):
        recipe = self.get_object()
        if not recipe:
            return Response(
                {'error': 'Recipe not found'}, status=status.HTTP_404_NOT_FOUND
            )
        user = request.user
        favorite_instance = Favorite.objects.filter(
            user=user, recipe=recipe
        ).first()

        if request.method == 'POST':
            if favorite_instance:
                return Response(
                    {'detail': 'Вы уже добавили в избранное этот рецепт.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            favorite_data = {
                'user': user.id,
                'recipe': recipe.id,
            }
            favorite_serializer = FavoriteSerializer(data=favorite_data)
            if favorite_serializer.is_valid():
                favorite_serializer.save()
                return Response(
                    FavoriteShoppingSerializer(
                        recipe, context={'request': request}
                    ).data,
                    status=status.HTTP_201_CREATED,
                )
            return Response(
                favorite_serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )
        if request.method == 'DELETE':
            if favorite_instance is not None:
                favorite_instance.delete()
                return Response(
                    {'message': 'Рецепт удален из избранного.'},
                    status=status.HTTP_204_NO_CONTENT,
                )
            return Response(
                {'message': 'Объект не найден.'},
                status=status.HTTP_404_NOT_FOUND,
            )

    @action(
        detail=True,
        methods=(
            'post',
            'delete',
        ),
        permission_classes=(permissions.IsAuthenticated,),
    )
    def shopping_cart(self, request, pk=None):
        recipe = self.get_object()
        if not recipe:
            return Response(
                {'error': 'Recipe not found'}, status=status.HTTP_404_NOT_FOUND
            )

        user = request.user
        shopping_instance = Shopping.objects.filter(
            user=user, recipe=recipe
        ).first()

        if request.method == 'POST':
            if shopping_instance:
                return Response(
                    {'detail': 'Вы уже добавили в корзину.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            shopping_data = {
                'user': user.id,
                'recipe': recipe.id,
            }
            shopping_serializer = ShoppingSerializer(data=shopping_data)
            if shopping_serializer.is_valid():
                shopping_serializer.save()
                return Response(
                    FavoriteShoppingSerializer(
                        recipe, context={'request': request}
                    ).data,
                    status=status.HTTP_201_CREATED,
                )
            else:
                return Response(
                    shopping_serializer.errors,
                    status=status.HTTP_400_BAD_REQUEST,
                )
        if request.method == 'DELETE':
            if shopping_instance is not None:
                shopping_instance.delete()
                return Response(
                    {'message': 'Рецепт удален из корзины.'},
                    status=status.HTTP_204_NO_CONTENT,
                )
            return Response(
                {'message': 'Объект не найден.'},
                status=status.HTTP_404_NOT_FOUND,
            )

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(permissions.IsAuthenticated,),
    )
    def download_shopping_cart(self, request):
        user = request.user

        total_ingredients = (
            RecipeIngredient.objects.filter(recipe__shopping__user=user)
            .values('ingredients__name', 'ingredients__measurement_unit')
            .annotate(total_amount=Sum('amount'))
        )

        response = HttpResponse(content_type=RESPONSE_CONTENT_TYPE)
        response[
            'Content-Disposition'
        ] = f"attachment; filename='{SHOPPING_CART_FILE_NAME}'"

        font_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'fonts/',
            'Verdana.ttf',
        )

        p = canvas.Canvas(response)
        pdfmetrics.registerFont(TTFont('Verdana', font_path))
        p.setFont('Verdana', 15)

        p.setFillColorRGB(0.2, 0.4, 0.6)
        p.rect(0, 805, 600, 40, fill=True)

        p.setFillColorRGB(1, 1, 1)
        p.drawString(210, 820, 'Корзина покупок:')

        y_position = 750

        p.setFillColorRGB(0, 0, 0)
        for ingredient_data in total_ingredients:
            ingredient = (
                f"{ingredient_data['ingredients__name']} "
                f"({ingredient_data['ingredients__measurement_unit']})"
            )
            amount = ingredient_data['total_amount']
            p.drawString(70, y_position, f'{ingredient} — {amount}')
            y_position -= 15

        p.setFillColorRGB(0.2, 0.4, 0.6)
        p.rect(0, 55, 600, 40, fill=True)

        p.setFillColorRGB(1, 1, 1)
        p.drawString(100, 70, ".-~*´¨¯¨`*·~-. ® «Фудграм» .-~*´¨¯¨`*·~-.")

        p.showPage()
        p.save()

        return response


class IngredientsViewSet(RetrieveListViewSet):
    '''Представление для ингредиентов.'''

    queryset = Ingredient.objects.all()
    serializer_class = IngredientsSerializer
    pagination_class = None
    filter_backends = (CustomIngredientsSearchFilter,)
    search_fields = ('^name',)


class ShoppingViewSet(viewsets.ModelViewSet):
    '''Представление для корзины.'''

    queryset = Shopping.objects.all()
    serializer_class = ShoppingSerializer


class UserCreateViewSet(UserViewSet):
    '''Представление для юзеров и подписки.'''

    queryset = User.objects.all()
    serializer_class = CreateUserSerializer

    def get_permissions(self):
        if self.action == 'retrieve' and self.kwargs.get('id'):
            return (permissions.AllowAny(),)
        return (permissions.AllowAny(),)

    @action(
        detail=True,
        methods=(
            'post',
            'delete',
        ),
        permission_classes=(permissions.IsAuthenticated,),
    )
    def subscribe(self, request, id=None):
        user = request.user
        follow_id = self.kwargs.get('id')
        following = get_object_or_404(User, id=follow_id)

        follow_instance = Follow.objects.filter(
            user=user, following=following
        ).first()
        if user == following:
            return Response(
                {'detail': 'Вы не можете подписаться на самого себя.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if request.method == 'POST':
            if follow_instance:
                return Response(
                    {'detail': 'Вы уже подписаны на этого пользователя.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            serializer_data = {'following': following.id}
            serializer = SubscribeSerializer(
                data=serializer_data, context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save(user=user, following=following)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            if follow_instance:
                follow_instance.delete()
                return Response(
                    {'message': 'Вы отписались.'},
                    status=status.HTTP_204_NO_CONTENT,
                )
            return Response(
                {'error': 'User is not in your followers'},
                status=status.HTTP_400_BAD_REQUEST,
            )


class UserFollowViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    '''Представление для отображения списка подписок.'''

    serializer_class = UserGetSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        current_user = self.request.user
        following_list = Follow.objects.filter(user=current_user).values_list(
            'following'
        )
        followed_users = User.objects.filter(id__in=following_list)

        recipes = Recipe.objects.filter(author__in=followed_users)

        self.request.followed_users_and_recipes = {'recipes': recipes}
        return followed_users
