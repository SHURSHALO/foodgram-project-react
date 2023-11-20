# Generated by Django 3.2.16 on 2023-11-17 14:59

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('food', '0013_auto_20231117_1758'),
    ]

    operations = [
        migrations.AddField(
            model_name='favorite',
            name='cooking_time',
            field=models.IntegerField(
                default=1,
                validators=[django.core.validators.MinValueValidator(1)],
                verbose_name='Время приготовления в мин.',
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='favorite',
            name='image',
            field=models.ImageField(
                default=1, upload_to='food/images', verbose_name='Фото'
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='favorite',
            name='name',
            field=models.CharField(
                default=1, max_length=255, verbose_name='Название'
            ),
            preserve_default=False,
        ),
    ]
