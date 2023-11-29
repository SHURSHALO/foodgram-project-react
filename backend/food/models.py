from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError

from backend.settings import (
    MIN_COOKING_TIME,
    MAX_COOKING_TIME,
    MIN_AMOUNT_COUNT,
    MAX_AMOUNT_COUNT,
)
from users.models import User


class Tag(models.Model):
    name = models.CharField(max_length=64, verbose_name='Название')
    color = models.CharField(max_length=16, verbose_name='Цвет')
    slug = models.SlugField(
        unique=True,
        verbose_name='Идентификатор',
        help_text='Идентификатор страницы для URL; '
        'разрешены символы латиницы, цифры, дефис и подчёркивание.',
    )

    class Meta:
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'

    def __str__(self):
        return self.name[:15]


class Ingredient(models.Model):
    name = models.CharField(max_length=255, verbose_name='Название')
    measurement_unit = models.CharField(
        max_length=16, verbose_name='Единицы измерения'
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = (
            models.UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='unique_name_measurement_unit',
            ),
        )

    def __str__(self):
        return self.name[:15]


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор рецепта',
        related_name='recipes',
    )
    name = models.CharField(max_length=255, verbose_name='Название')
    image = models.ImageField(upload_to='food/images', verbose_name='Фото')

    text = models.TextField(verbose_name='Текст')
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        verbose_name='Ингредиенты',
        related_name='recipe',
    )
    tags = models.ManyToManyField(
        Tag, verbose_name='Тэги', related_name='recipe'
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления в мин.',
        validators=[
            MinValueValidator(MIN_COOKING_TIME),
            MaxValueValidator(MAX_COOKING_TIME),
        ],
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.text[:15]


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipies',
        verbose_name='Рецепт',
    )
    ingredients = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredients',
        verbose_name='Ингредиент',
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество',
        validators=(
            MinValueValidator(MIN_AMOUNT_COUNT),
            MaxValueValidator(MAX_AMOUNT_COUNT),
        ),
    )

    class Meta:
        verbose_name = 'Связь рецепта и ингредиента'
        verbose_name_plural = 'Связь рецептов и ингредиентов'


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='favorites',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorite',
        verbose_name='Рецепт',
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'), name='unique_user_recipes'
            ),
        )


class Shopping(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='shopping',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shopping',
        verbose_name='Рецепт',
    )

    class Meta:
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзины'
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'), name='unique_user_recipe'
            ),
        )


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='followers',
        verbose_name='Текущий пользователь',
    )

    following = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='На кого подписан',
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'following'), name='unique_user_following'
            ),
        )

    def clean(self):
        if self.user == self.following:
            raise ValidationError("Вы не можете подписаться на самого себя.")

    def __str__(self):
        return f'{self.user.username} - {self.following.username}'
