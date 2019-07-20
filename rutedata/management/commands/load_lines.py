from django.core.management.base import BaseCommand

from rutedata.load_xml.LoadLines import LoadLines


class Command(BaseCommand):
    help = 'Import lines from XML'

    def handle(self, *args, **options):
        # Lines
        load = LoadLines()
        load.load_lines(output=True)
