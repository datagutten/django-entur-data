from django.core.management.base import BaseCommand

from rutedata.load_xml.LoadStopPoints import LoadStopPoints


class Command(BaseCommand):
    help = 'Importerer holdeplasser fra XML'

    def handle(self, *args, **options):
        loader = LoadStopPoints()
        loader.load_stop_points()
