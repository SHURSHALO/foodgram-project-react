# Generated by Django 3.2.16 on 2023-11-28 15:04

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('food', '0003_auto_20231128_1656'),
    ]

    operations = [
        migrations.AlterField(
            model_name='recipeingredient',
            name='ingredients',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='recipeingredients',
                to='food.ingredient',
                verbose_name='Ингредиент',
            ),
        ),
        migrations.AlterField(
            model_name='recipeingredient',
            name='recipe',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='recipeingredients',
                to='food.recipe',
                verbose_name='Рецепт',
            ),
        ),
    ]
