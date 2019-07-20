from django.core.management.base import BaseCommand

from rutedata.load_xml.LoadLines import LoadLines


class Command(BaseCommand):
    help = 'Importerer ruter for en linje fra XML'

    def handle(self, *args, **options):
        loader = LoadLines()
        loader.load_lines()
