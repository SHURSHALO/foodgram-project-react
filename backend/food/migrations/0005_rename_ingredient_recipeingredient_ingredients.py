# Generated by Django 3.2.16 on 2023-11-16 18:55

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('food', '0004_rename_count_recipeingredient_amount'),
    ]

    operations = [
        migrations.RenameField(
            model_name='recipeingredient',
            old_name='ingredient',
            new_name='ingredients',
        ),
    ]
