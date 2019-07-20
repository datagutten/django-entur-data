from django.core.management.base import BaseCommand
from rutedata.load_xml.LoadStops import LoadStops


class Command(BaseCommand):
    help = 'Load Stops and Quays'

    def handle(self, *args, **options):
        # Stops and Quays per region – Current stops
        load = LoadStops()
        load.load_stops()
        load.load_groups()
