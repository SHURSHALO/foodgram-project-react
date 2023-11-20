from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Модель пользователя с расширенным функционалом для Django приложения."""

    REQUIRED_FIELDS = ('username', 'first_name', 'last_name')
    USERNAME_FIELD = 'email'

    username = models.CharField(
        max_length=150,
        unique=True,
        db_index=True,
        blank=True,
        error_messages={
            'unique': 'Пользователь с таким именем уже существует.',
        },
    )
    email = models.EmailField(
        verbose_name='Электронная почта',
        max_length=254,
        unique=True,
        error_messages={
            'unique': 'Пользователь с такой почтой уже существует.',
        },
    )
    first_name = models.CharField(verbose_name='Имя', max_length=150)
    last_name = models.CharField(verbose_name='Фамилия', max_length=150)

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
