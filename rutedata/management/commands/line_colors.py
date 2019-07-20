import json

from django.core.management.base import BaseCommand

from rutedata.models import Line


class Command(BaseCommand):
    help = 'Generate line colors'

    def handle(self, *args, **options):
        fp = open('colors.json', 'w')
        lines = Line.objects.all()
        colours = dict()
        for line in lines:
            print(line.id)
            print(line.Colour)
            colours[line.id] = line.Colour
        json.dump(colours, fp)
        fp.close()
