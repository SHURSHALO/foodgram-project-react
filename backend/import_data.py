import os
import django
import pandas as pd
from food.models import Ingredient

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()


def import_data(csv_path):
    df = pd.read_csv(csv_path)

    for index, row in df.iterrows():
        Ingredient.objects.create(
            name=row['name'], measurement_unit=row['measurement_unit']
        )


if __name__ == "__main__":
    import_data('C:/Dev/foodgram-project-react/data/ingredients.csv')
