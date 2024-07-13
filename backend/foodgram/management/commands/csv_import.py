import csv
from django.core.management.base import BaseCommand

from foodgram.models import Ingredient, Tag


models = {
    "ingredients": Ingredient,
    "tags": Tag
}


class Command(BaseCommand):
    help = "Import csv files from data/"

    def add_arguments(self, parser):
        parser.add_argument("file_name", nargs=1, type=str)

    def handle(self, **options):
        search_file = "data/" + options["file_name"][0] + ".csv"
        model = models[options["file_name"][0]]

        with open(search_file, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                model.objects.create(**row)
