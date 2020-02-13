from django.core.management.base import BaseCommand
from rutedata.load_xml.LoadStops import LoadStops


class Command(BaseCommand):
    help = 'Load Stops and Quays'

    def add_arguments(self, parser):
        parser.add_argument('file', nargs='?', type=str)

    def handle(self, *args, **options):
        # Stops and Quays per region – Current stops
        if options['file']:
            load = LoadStops(file=options['file'])
        else:
            load = LoadStops()
        load.load_stops()
        load.load_groups()
