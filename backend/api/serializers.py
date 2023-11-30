import base64
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.db import transaction
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from backend.settings import (
    REGEX_USERNAME,
    MIN_COOKING_TIME,
    MAX_COOKING_TIME,
    MIN_INGREDIENTS_COUNT,
    MAX_INGREDIENTS_COUNT,
    MIN_AMOUNT_COUNT,
    MAX_AMOUNT_COUNT,
)
from food.models import (
    Favorite,
    Follow,
    Ingredient,
    Recipe,
    RecipeIngredient,
    Shopping,
    Tag,
)
from users.models import User
from api.validators import validate_email, validate_username


class CreateUserSerializer(serializers.ModelSerializer):
    '''Сериализатор для юзера.'''

    email = serializers.EmailField(
        max_length=254,
        required=True,
    )
    username = serializers.RegexField(
        regex=REGEX_USERNAME,
        max_length=150,
        required=True,
    )
    is_subscribed = serializers.SerializerMethodField()
    password = serializers.CharField(
        write_only=True,
        required=True,
    )

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'password',
        )
        validators = (
            validate_email,
            validate_username,
        )

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            return Follow.objects.filter(user=user, following=obj).exists()
        return False


class Base64ImageField(serializers.ImageField):
    '''Сериализатор для обработки картинок.'''

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class TagsSerializer(serializers.ModelSerializer):
    '''Сериализатор для тэгов.'''

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientsSerializer(serializers.ModelSerializer):
    '''Сериализатор для ингредиентов.'''

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')

        validators = (
            UniqueTogetherValidator(
                queryset=Ingredient.objects.all(),
                fields=('name'),
                message='Этот ингредиент уже существует.',
            ),
        )


class RecipeIngridientsSerializer(serializers.ModelSerializer):
    '''Сериализатор для связи рецепта ингредиента'''

    id = serializers.PrimaryKeyRelatedField(
        source='ingredients.id', queryset=Ingredient.objects.all()
    )
    measurement_unit = serializers.CharField(
        source='ingredients.measurement_unit', read_only=True
    )
    name = serializers.CharField(source='ingredients.name', read_only=True)

    class Meta:
        model = RecipeIngredient
        fields = (
            'id',
            'name',
            'measurement_unit',
            'amount',
        )


class RecipeIngredientAmountSerializer(serializers.ModelSerializer):
    '''Сериализатор для принятия запроса ингредиета в сериализаторе рецепта.'''

    id = serializers.IntegerField()
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeDetailSerializer(serializers.ModelSerializer):
    '''Сериализатор для получения рецепта.'''

    author = CreateUserSerializer(read_only=True)
    tags = TagsSerializer(many=True, read_only=True)
    ingredients = RecipeIngridientsSerializer(
        many=True, read_only=True, source='recipies'
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            return Favorite.objects.filter(user=user, recipe=obj).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            return Shopping.objects.filter(user=user, recipe=obj).exists()
        return False


class RecipeSerializer(serializers.ModelSerializer):
    '''Сериализатор для создания рецепта.'''

    author = serializers.PrimaryKeyRelatedField(
        read_only=True, default=serializers.CurrentUserDefault()
    )
    ingredients = RecipeIngredientAmountSerializer(
        many=True, source='recipies'
    )
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all()
    )
    image = Base64ImageField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def validate_cooking_time(self, value):
        if value < MIN_COOKING_TIME or value > MAX_COOKING_TIME:
            raise ValidationError(
                f'Время готовки должно быть '
                f'от {MIN_COOKING_TIME} до {MAX_COOKING_TIME} минут.'
            )
        return value

    def validate_ingredients(self, value):
        ingredient_ids = set()
        for ingredient in value:
            if (
                not MIN_AMOUNT_COUNT
                <= ingredient['amount']
                <= MAX_AMOUNT_COUNT
            ):
                raise ValidationError(
                    f'Количество ингредиента должно быть '
                    f'от {MIN_AMOUNT_COUNT} до {MAX_AMOUNT_COUNT}. '
                )
            if ingredient['id'] in ingredient_ids:
                raise ValidationError('Ингредиенты не должны повторяться.')
            ingredient_ids.add(ingredient['id'])
        return value

    def validate_ingredient_count(self, ingredients_data):
        if (
            len(ingredients_data) < MIN_INGREDIENTS_COUNT
            or len(ingredients_data) > MAX_INGREDIENTS_COUNT
        ):
            raise ValidationError(
                f'Количество ингредиентов должно быть '
                f'от {MIN_INGREDIENTS_COUNT} до {MAX_INGREDIENTS_COUNT}.'
            )
        return ingredients_data

    def validate(self, data):
        ingredients_data = data.get('recipies', [])
        self.validate_ingredient_count(ingredients_data)
        return data

    @transaction.atomic
    def create(self, validated_data):
        ingredients_data = validated_data.pop('recipies')
        tags_data = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)

        for meaning in ingredients_data:
            ingredient_id = meaning.get('id')
            amount = meaning.get('amount')

            ingredient_instance = Ingredient.objects.get(pk=ingredient_id)
            recipe_ingredient = RecipeIngredient.objects.create(
                recipe=recipe,
                ingredients=ingredient_instance,
                amount=amount,
            )
            recipe_ingredient.save()

        recipe.tags.set(tags_data)

        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.image = validated_data.get('image', instance.image)
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time
        )

        instance.save()

        ingredients_data = validated_data.get('ingredients')
        if ingredients_data:
            instance.recipies.all().delete()

            for ingredient_data in ingredients_data:
                ingredient_id = ingredient_data.get('id')
                amount = ingredient_data.get('amount')
                ingredient_instance = Ingredient.objects.get(pk=ingredient_id)
                recipe_ingredient = RecipeIngredient.objects.create(
                    recipe=instance,
                    ingredients=ingredient_instance,
                    amount=amount,
                )
                recipe_ingredient.save()

        tags_data = validated_data.get('tags')
        if tags_data is not None:
            instance.tags.set(tags_data)

        return instance

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            return Favorite.objects.filter(user=user, recipe=obj).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            return Shopping.objects.filter(user=user, recipe=obj).exists()
        return False

    def to_representation(self, instance):
        request = self.context.get('request')
        serializer = RecipeDetailSerializer(
            instance, context={'request': request}
        )
        return serializer.data


class FavoriteShoppingSerializer(serializers.ModelSerializer):
    '''Сериализатор для связи избранное корзина.'''

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class FavoriteSerializer(serializers.ModelSerializer):
    '''Сериализатор для избранного.'''

    class Meta:
        model = Favorite
        fields = ('id', 'user', 'recipe')

        validators = (
            UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=('user', 'recipe'),
                message='Вы уже добавили в избранное.',
            ),
        )


class ShoppingSerializer(serializers.ModelSerializer):
    '''Сериализатор для корзины.'''

    class Meta:
        model = Shopping
        fields = ('id', 'user', 'recipe')

        validators = (
            UniqueTogetherValidator(
                queryset=Shopping.objects.all(),
                fields=('user', 'recipe'),
                message='Вы уже добавили в корзину.',
            ),
        )


class RecipeSubscribeSerializer(serializers.ModelSerializer):
    '''Сериализатор для связи рецепты подписок.'''

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscribeSerializer(CreateUserSerializer):
    '''Сериализатор для подписки.'''

    email = serializers.EmailField(source='following.email', read_only=True)
    first_name = serializers.CharField(
        source='following.first_name', read_only=True
    )
    last_name = serializers.CharField(
        source='following.last_name', read_only=True
    )
    username = serializers.CharField(
        source='following.username', read_only=True
    )
    is_subscribed = serializers.SerializerMethodField()
    recipes = RecipeSubscribeSerializer(
        many=True, read_only=True, source='following.recipes'
    )
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = Follow
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
        )

    def get_recipes_count(self, obj):
        return obj.following.recipes.count()

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        following_user = obj.following

        if user == following_user:
            raise serializers.ValidationError(
                "Вы не можете подписаться на самого себя."
            )

        return Follow.objects.filter(
            user=user, following=following_user
        ).exists()


class UserGetSerializer(serializers.ModelSerializer):
    '''Сериализатор для просмотра подписок.'''

    is_subscribed = serializers.SerializerMethodField()
    recipes = RecipeSubscribeSerializer(many=True, read_only=True)
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
        )

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            return Follow.objects.filter(user=user, following=obj).exists()
        return False

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        recipes_limit = self.context.get('request').query_params.get(
            'recipes_limit'
        )

        if recipes_limit:
            try:
                recipes_limit_int = int(recipes_limit)
                if recipes_limit_int <= 0:
                    raise ValueError(
                        "recipes_limit должен быть положительным числом"
                    )

                data['recipes'] = data['recipes'][:recipes_limit_int]
            except ValueError:
                data['error'] = 'Неверное значение для recipes_limit'

        return data
