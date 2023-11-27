import base64
from backend.settings import (
    REGEX_USERNAME,
    MIN_COOKING_TIME,
    MAX_COOKING_TIME,
    MIN_INGREDIENTS_COUNT,
    MAX_INGREDIENTS_COUNT,
)
from django.core.files.base import ContentFile
from django.core.exceptions import ValidationError
from django.db import transaction
from rest_framework import serializers

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
from api.validators import validate_email, validate_me, validate_username


class CreateUserSerializer(serializers.ModelSerializer):
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
            validate_me,
            validate_email,
            validate_username,
        )

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            return Follow.objects.filter(user=user, following=obj).exists()


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class TagsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngridientsSerializer(serializers.ModelSerializer):
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
    id = serializers.IntegerField()
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeDetailSerializer(serializers.ModelSerializer):
    author = CreateUserSerializer(read_only=True)
    tags = TagsSerializer(many=True, read_only=True)
    ingredients = RecipeIngridientsSerializer(
        many=True, read_only=True, source='recipeingredients'
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

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            return Shopping.objects.filter(user=user, recipe=obj).exists()


class RecipeSerializer(serializers.ModelSerializer):
    author = serializers.PrimaryKeyRelatedField(
        read_only=True, default=serializers.CurrentUserDefault()
    )
    ingredients = RecipeIngredientAmountSerializer(
        many=True, source='recipeingredients'
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
                'Время готовки должно быть от 1 до 1000 минут.'
            )
        return value

    def validate_ingredients(self, value):
        ingredient_ids = set()
        for ingredient in value:
            if ingredient['amount'] <= 0:
                raise ValidationError(
                    'Количество ингредиента должно быть больше 0.'
                )
            if ingredient['id'] in ingredient_ids:
                raise ValidationError('Ингредиенты не должны повторяться.')
            ingredient_ids.add(ingredient['id'])
        return value

    def validate(self, data):
        ingredients_data = data.get('recipeingredients', [])
        if (
            len(ingredients_data) < MIN_INGREDIENTS_COUNT
            or len(ingredients_data) > MAX_INGREDIENTS_COUNT
        ):
            raise ValidationError(
                'Количество ингредиентов должно быть от 1 до 20.'
            )
        return data

    def create(self, validated_data):
        with transaction.atomic():
            ingredients_data = validated_data.pop('recipeingredients')
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

    def update(self, instance, validated_data):
        with transaction.atomic():
            instance.name = validated_data.get('name', instance.name)
            instance.text = validated_data.get('text', instance.text)
            instance.image = validated_data.get('image', instance.image)
            instance.cooking_time = validated_data.get(
                'cooking_time', instance.cooking_time
            )

            instance.save()

            ingredients_data = validated_data.get('ingredients')
            if ingredients_data:
                instance.recipeingredients.all().delete()

                for ingredient_data in ingredients_data:
                    ingredient_id = ingredient_data.get('id')
                    amount = ingredient_data.get('amount')
                    ingredient_instance = Ingredient.objects.get(
                        pk=ingredient_id
                    )
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

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            return Shopping.objects.filter(user=user, recipe=obj).exists()

    def to_representation(self, instance):
        request = self.context.get('request')
        serializer = RecipeDetailSerializer(
            instance, context={'request': request}
        )
        return serializer.data


class FavoriteShoppingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = ('id', 'user', 'recipe')


class ShoppingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shopping
        fields = ('id', 'user', 'recipe')


class RecipeSubscribeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscribeSerializer(CreateUserSerializer):
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
        model = Follow

    def get_recipes_count(self, obj):
        return obj.following.recipes.count()

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        return Follow.objects.filter(
            user=user, following=obj.following
        ).exists()


class UserGetSerializer(serializers.ModelSerializer):
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

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        recipes_limit = self.context.get('request').query_params.get(
            'recipes_limit'
        )
        if recipes_limit:
            data['recipes'] = data['recipes'][: int(recipes_limit)]

        return data
