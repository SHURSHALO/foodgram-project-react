# Generated by Django 3.2.16 on 2023-11-16 12:25

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('food', '0003_auto_20231116_1440'),
    ]

    operations = [
        migrations.RenameField(
            model_name='recipeingredient',
            old_name='count',
            new_name='amount',
        ),
    ]
