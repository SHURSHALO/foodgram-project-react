# Generated by Django 3.2.16 on 2023-11-17 12:12

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('food', '0007_alter_recipe_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='favorite',
            name='image',
            field=models.ImageField(
                upload_to='food/images', verbose_name='Фото'
            ),
        ),
        migrations.AlterField(
            model_name='favorite',
            name='recipe',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='favorite',
                to='food.recipe',
            ),
        ),
    ]
