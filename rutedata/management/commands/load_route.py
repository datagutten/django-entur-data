import re
import xml.etree.ElementTree

from django.core.management.base import BaseCommand

from rutedata.models import Line, PointOnRoute, Quay, Route


class Command(BaseCommand):
    help = 'Importerer holdeplasser fra XML'

    # def add_arguments(self, parser):
    #   parser.add_argument('daysonly', nargs='+')

    def handle(self, *args, **options):
        # tree = xml.etree.ElementTree.parse('rb_rut-aggregated-netex/RUT_RUT-Line-83_83_Radhuset---Tarnasen.xml')
        tree = xml.etree.ElementTree.parse('rb_rut-aggregated-netex/RUT_RUT-Line-11_11_Majorstuen---Storo-Grefsen-st-.xml')
        root = tree.getroot()
        namespaces = {'netex': 'http://www.netex.org.uk/netex'}
        # routes = tree.findall('.//netex:Route', namespaces)
        for route in root.findall('.//netex:frames/netex:ServiceFrame/netex:routes/netex:Route', namespaces):
            line_id = id=route.find('netex:LineRef', namespaces).attrib['ref']
            # line = Line.objects.filter(line_id)
            # if line.count() == 0:
            #    raise Line.DoesNotExist('Line not found')
            # line = line.first()
            line = Line.objects.get(line_id)
            # line = line[0]

            # print(line)
            # break;
            route_db = Route(
                id=route.attrib['id'],
                Name=route.find('netex:Name', namespaces).text,
                ShortName=route.find('netex:ShortName', namespaces).text,
                LineRef=line,
            )
            route_db.save()
            # print (route_db)
            # break
            for point in route.findall('./netex:pointsInSequence/netex:PointOnRoute', namespaces):
                # print(point)

                StopPointId = (
                    re.search('[A-Z]+:RoutePoint:([A-Za-z0-9\-]+)', point.find('netex:RoutePointRef', namespaces).attrib['ref']))
                StopPointId = StopPointId[1]
                # StopPoint_db = StopPoint.objects.filter(id=StopPointId)[0]
                # StopPoint_db = StopPoint.objects.get(id=StopPointId)

                prefixed_id = point.find('netex:RoutePointRef', namespaces).get('ref')
                point_id = re.sub(r'[A-Z]+:RoutePoint:[A-Za-z]+-([0-9]+)', r'\1', prefixed_id)
                try:
                    quay = Quay.objects.get(id=point_id)
                except Quay.DoesNotExist:
                    print('Quay %s does not exist' % point_id)
                    break

                point_db = PointOnRoute(
                    id=point.attrib['id'],
                    RouteId=route_db,
                    order=point.attrib['order'],
                    # StopPointRef=StopPoint_db,
                    quay=quay,
                )
                if point.attrib['order'] == '1':
                    route_db.origin = quay
                    route_db.save()
                # print(point_db)
                point_db.save()
                # break
            print(quay)
            route_db.destination = quay
            route_db.save()
