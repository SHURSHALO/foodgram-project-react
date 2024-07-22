import os
import django
import pandas as pd

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from food.models import Tag


def import_data(csv_path):
    df = pd.read_csv(csv_path)

    for index, row in df.iterrows():
        Tag.objects.create(
            name=row['name'], color=row['color'], slug=row['slug']
        )


if __name__ == "__main__":
    data_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'data/',
        'tags.csv',
    )

    import_data(data_path)