import os

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from django.db.models import F
from rest_framework import (
    filters,
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

from api.filters import RecipeFilter
from api.permissions import AuthorOrReadOnly
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


class RetrieveListViewSet(
    mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet
):
    pass


class TagsViewSet(RetrieveListViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagsSerializer
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.annotate(created_at=F('id')).order_by(
        '-created_at'
    )
    serializer_class = RecipeSerializer
    permission_classes = (AuthorOrReadOnly,)
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return (permissions.AllowAny(),)

        return super().get_permissions()

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeDetailSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[permissions.IsAuthenticated],
    )
    def favorite(self, request, pk=None):
        recipe = self.get_object()
        if not recipe:
            return Response(
                {"error": "Recipe not found"}, status=status.HTTP_404_NOT_FOUND
            )
        user = request.user
        favorite_instance = Favorite.objects.filter(
            user=user, recipe=recipe
        ).first()

        if request.method == 'POST':
            if Favorite.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {"detail": "Вы уже добавили в избранное этот рецепт."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            favorite_data = {
                "recipe": recipe.id,
                "user": user.id,
                "name": recipe.name,
                "image": recipe.image,
                "cooking_time": recipe.cooking_time,
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
            else:
                return Response(
                    favorite_serializer.errors,
                    status=status.HTTP_400_BAD_REQUEST,
                )
        if request.method == 'DELETE':
            favorite_instance.delete()
            return Response(
                {"message": "Рецепт удален из избранного."},
                status=status.HTTP_204_NO_CONTENT,
            )

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[permissions.IsAuthenticated],
    )
    def shopping_cart(self, request, pk=None):
        recipe = self.get_object()
        if not recipe:
            return Response(
                {"error": "Recipe not found"}, status=status.HTTP_404_NOT_FOUND
            )

        user = request.user
        shopping_instance = Shopping.objects.filter(
            user=user, recipe=recipe
        ).first()

        if request.method == 'POST':
            shopping_data = {
                "recipe": recipe.id,
                "user": user.id,
                "name": recipe.name,
                "image": recipe.image,
                "cooking_time": recipe.cooking_time,
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
            shopping_instance.delete()
            return Response(
                {"message": "Рецепт удален из корзины."},
                status=status.HTTP_204_NO_CONTENT,
            )

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[permissions.IsAuthenticated],
    )
    def download_shopping_cart(self, request):
        user = request.user

        shopping_list = Shopping.objects.filter(user=user)

        total_ingredients = {}

        for item in shopping_list:
            for recipe_ingredient in RecipeIngredient.objects.filter(
                recipe=item.recipe
            ):
                ingredient = recipe_ingredient.ingredients
                ingredient_key = (
                    f"{ingredient.name} ({ingredient.measurement_unit})"
                )
                total_ingredients[ingredient_key] = (
                    total_ingredients.get(ingredient_key, 0)
                    + recipe_ingredient.amount
                )

        response = HttpResponse(content_type='application/pdf')
        response[
            'Content-Disposition'
        ] = 'attachment; filename="shopping_cart.pdf"'

        font_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'fonts/',
            'Verdana.ttf',
        )

        p = canvas.Canvas(response)
        pdfmetrics.registerFont(TTFont('Verdana', font_path))
        p.setFont("Verdana", 15)

        p.setFillColorRGB(0.2, 0.4, 0.6)
        p.rect(0, 805, 600, 40, fill=True)

        p.setFillColorRGB(1, 1, 1)
        p.drawString(210, 820, "Корзина покупок:")

        y_position = 750

        p.setFillColorRGB(0, 0, 0)
        for ingredient, amount in total_ingredients.items():
            p.drawString(70, y_position, f"{ingredient} — {amount}")
            y_position -= 15

        p.setFillColorRGB(0.2, 0.4, 0.6)
        p.rect(0, 55, 600, 40, fill=True)

        p.setFillColorRGB(1, 1, 1)
        p.drawString(100, 70, ".-~*´¨¯¨`*·~-. ® «Фудграм» .-~*´¨¯¨`*·~-.")

        p.showPage()
        p.save()

        return response


class IngredientsViewSet(RetrieveListViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientsSerializer
    pagination_class = None
    filter_backends = (filters.SearchFilter,)
    search_fields = ('^name',)


class ShoppingViewSet(viewsets.ModelViewSet):
    queryset = Shopping.objects.all()
    serializer_class = ShoppingSerializer


class UserCreateViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = CreateUserSerializer

    def get_permissions(self):
        if self.action == 'retrieve' and self.kwargs.get('id'):
            return [permissions.AllowAny()]
        return super().get_permissions()

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[permissions.IsAuthenticated],
    )
    def subscribe(self, request, id=None):
        user = request.user
        follow_id = self.kwargs.get('id')
        print(follow_id)
        following = get_object_or_404(User, id=follow_id)

        follow_instance = Follow.objects.filter(
            user=user, following=following
        ).first()
        if user == following:
            return Response(
                {"detail": "Вы не можете подписаться на самого себя."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if request.method == 'POST':
            if Follow.objects.filter(user=user, following=following).exists():
                return Response(
                    {"detail": "Вы уже подписаны на этого пользователя."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            serializer_data = {'following': following.id}
            serializer = SubscribeSerializer(
                data=serializer_data, context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save(user=user, following=following)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            if follow_instance:
                follow_instance.delete()
                return Response(
                    {"message": "Вы отписались."},
                    status=status.HTTP_204_NO_CONTENT,
                )
            else:
                return Response(
                    {"error": "User is not in your followers"},
                    status=status.HTTP_400_BAD_REQUEST,
                )


class UserFollowViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
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
