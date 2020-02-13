import re
import xml.etree.ElementTree

from rutedata.models import Line, PassingTime, PointOnRoute, Quay, Route, ServiceJourney
from .line_helper import LineHelper
from .load_xml import LoadXml


class LoadLines(LoadXml):
    skip = []
    line_db = None

    def __init__(self):
        self.helper = LineHelper()

    def load_line(self, root):
        """
        Load Line
        :param root:
        :return:
        """
        for line in root.findall('.//netex:lines/netex:Line', self.namespaces):
            line_db = Line(id=line.attrib['id'],
                           Name=line.find('netex:Name', self.namespaces).text,
                           TransportMode=line.find('netex:TransportMode', self.namespaces).text,
                           PublicCode=line.find('netex:PublicCode', self.namespaces).text,
                           Colour=line.find('./netex:Presentation/netex:Colour', self.namespaces).text)
            line_db.save()
            self.line_db = line_db
            return line_db

    def load_route(self, root):
        """
        Load Route
        Requires Line
        Deletes PointOnRoute
        :param root:
        :return:
        """
        for route in root.findall('.//netex:frames/netex:ServiceFrame/netex:routes/netex:Route', self.namespaces):
            line_id = route.find('netex:LineRef', self.namespaces).attrib['ref']
            line = Line.objects.get(id=line_id)

            points_delete = PointOnRoute.objects.filter(Route__id=route.attrib['id'])
            points_delete.all().delete()

            route_db = Route(
                id=route.attrib['id'],
                Name=route.find('netex:Name', self.namespaces).text,
                ShortName=route.find('netex:ShortName', self.namespaces).text,
                LineRef=line,
            )
            route_db.save()
            self.load_point_on_route(route, route_db)

    def load_point_on_route(self, route, route_db):
        """
        Load RoutePoint
        Called in loop by load_route()
        Route and Quay must be loaded before this
        :param route:
        :param route_db:
        :return:
        """

        for point in route.findall(
                './netex:pointsInSequence/netex:PointOnRoute',
                self.namespaces):

            prefixed_id = point.find('netex:RoutePointRef',
                                     self.namespaces).get('ref')

            """"RoutePoint is defined in _RUT_shared_data.xml with a relation to ScheduledStopPoint
            ScheduledStopPoint has a relation to Quay in PassengerStopAssignment element
            The numeric id is the same for all of these"""

            point_id = re.sub(r'[A-Z]+:RoutePoint:[A-Za-z]+-([0-9]+)',
                              r'\1', prefixed_id)
            quay_id = 'NSR:Quay:%s' % point_id
            # StopPoint_db = StopPoint.objects.get(id=point_id)
            try:
                quay = Quay.objects.get(id=quay_id)
            except Quay.DoesNotExist as e:
                # Quay might be outside loaded area
                print('Quay %s does not exist' % quay_id)
                self.skip.append(route_db.id)
                PointOnRoute.objects.filter(Route=route_db).delete()
                raise e

            point_db = PointOnRoute(
                id=point.attrib['id'],
                Route=route_db,
                order=point.attrib['order'],
                quay=quay,
            )
            point_db.save()

    def load_service_journeys(self, root, output=False):
        """
        Load ServiceJourney
        Requires Line, Route
        :param root:
        :param output:
        :return:
        """
        print('Loading ServiceJourney and PassingTime')
        valid_journeys = []
        lines = []
        journeys = root.findall(
                './/netex:frames/netex:TimetableFrame/netex:vehicleJourneys/netex:ServiceJourney',
                self.namespaces)
        total = len(journeys)
        count = 1

        existing_journeys = self.existing_service_journeys(self.line_db)

        for journey in journeys:
            if output:
                print('Loading %d of %d' % (count, total), end='\r')
            count += 1
            journey_id = journey.get('id')
            if journey_id in existing_journeys:
                index = existing_journeys.index(journey_id)
                existing_journeys.pop(index)
                continue
            print(journey_id)
            valid_journeys.append(journey_id)

            # name = journey.find('netex:Name', self.namespaces).text
            name = self.text(journey, 'Name')
            private_code = self.text(journey, 'PrivateCode')

            # private_code = journey.find('netex:PrivateCode', self.namespaces).text
            line_ref = journey.find('netex:LineRef', self.namespaces).get('ref')
            line_ref = self.get(journey, 'LineRef')
            try:
                line = Line.objects.get(id=line_ref)
            except Line.DoesNotExist as e:
                print('Line %s does not exist' % line_ref)
                raise e
            lines.append(line)

            journey_pattern = self.helper.journey_pattern(
                root,
                self.get(journey, 'JourneyPatternRef')
            )
            route_ref = self.get(journey_pattern, 'RouteRef')
            try:
                route = Route.objects.get(id=route_ref)
            except Route.DoesNotExist:
                raise ValueError('Route %s does not exist' % route_ref)
                return

            journey_db = ServiceJourney(id=journey_id,
                                        name=name,
                                        private_code=private_code,
                                        line=line,
                                        route=route)
            journey_db.save()
            self.load_passings(journey=journey, journey_db=journey_db)
        if output:
            print("")
        print('Journeys not found: ', existing_journeys)
        self.cleanup_journeys(lines, valid_journeys)

    @staticmethod
    def cleanup_journeys(lines, valid_journeys):
        for line in lines:
            for journey in ServiceJourney.objects.filter(line=line):
                if journey.id not in valid_journeys:
                    print('Invalid journey: %s' % journey.id)
                    journey.delete()

    def existing_passings(self, journey_db):
        passings = PassingTime.objects.filter(service_journey=journey_db).values_list('id', flat=True)
        return list(passings)

    def existing_service_journeys(self, line_db):
        journeys = ServiceJourney.objects.filter(line=line_db).values_list('id', flat=True)
        return list(journeys)

    def load_passings(self, journey, journey_db=None, output=False):
        """
        Load PassingTime
        Called in loop by load_service_journeys
        Requires PointOnRoute
        :param xml.etree.ElementTree.Element journey:
        :param ServiceJourney journey_db:
        :param bool output: Show output
        :return:
        """

        passings = journey.findall(
            './/netex:passingTimes/netex:TimetabledPassingTime',
            self.namespaces)
        if journey_db is None:
            journey_db = ServiceJourney.objects.get(id=journey.get('id'))

        existing = self.existing_passings(journey_db)

        if not passings:
            raise ValueError('No passings found')
        count = 1
        total = len(passings)

        if output:
            print('%d passings in DB and %d in file' % (len(existing), total))
            print("")

        if len(existing) == total:
            return

        for timetabled_passing_time in passings:
            if output:
                print('Loading passing %d of %d                    ' % (count, total), end='\r')
            journey_id = timetabled_passing_time.get('id')
            point_ref = timetabled_passing_time.find('netex:StopPointInJourneyPatternRef',
                                                     self.namespaces).get('ref')

            # Convert RUT:StopPointInJourneyPattern:86-2-16 to RUT:Route:86-2
            keys = re.match(r'([A-Z]+):StopPointInJourneyPattern:([0-9]+\-[0-9]+)\-([0-9]+)', point_ref)
            route_id = '%s:Route:%s' % (keys[1], keys[2])

            try:
                point = PointOnRoute.objects.get(Route__id=route_id, order=keys[3])
            except PointOnRoute.MultipleObjectsReturned as e:
                print('Multiple PointOnRoute found: Route__id=%s, order=%s' % (route_id, keys[3]))
                raise e
            except PointOnRoute.DoesNotExist as e:
                print('PointOnRoute with Route__id %s and order %s does not exist' % (route_id, keys[3]))
                continue

            passing = PassingTime(id=journey_id,
                                  service_journey=journey_db,
                                  point=point,
                                  line=journey_db.line,
                                  )

            departure = timetabled_passing_time.find('netex:DepartureTime', self.namespaces)
            if departure is not None:
                passing.departure_time = self.parse_time(departure.text)
            arrival = timetabled_passing_time.find('netex:ArrivalTime', self.namespaces)
            if arrival is not None:
                passing.arrival_time = self.parse_time(arrival.text)

            count += 1
            passing.save()

    def load_passings_journeys(self, line_root, output=False):
        journeys = self.helper.vehicle_journeys(line_root)
        total = len(journeys)

        count = 1
        for journey in journeys:
            if output:
                print('Loading passings for journey %d of %d' % (count, total), end='\r')

            self.load_passings(journey=journey, output=False)
            count += 1

    def load_lines(self, line_filter=None, load_lines=True, load_routes=True, load_service_journeys=True, load_passings_journeys=True, output=False):
        zip_file = self.load_netex(None)
        for file in zip_file.namelist():
            if file.find('RUT_RUT-Line') == -1:
                continue
            if line_filter and file.find(line_filter) == -1:
                continue
            if output:
                print(file)
            xml_bytes = zip_file.read(file)
            root = xml.etree.ElementTree.fromstring(xml_bytes)
            self.line_db = self.load_line(root)

            try:
                if load_routes:
                    self.load_route(root)
                if load_service_journeys:
                    self.load_service_journeys(root, output)
                # journey = ServiceJourney.objects.get(id='RUT:ServiceJourney:83-116601-13185420')
                # self.load_passings(root=root, journey_db=journey)
                if load_passings_journeys:
                    self.load_passings_journeys(root)
            except Quay.DoesNotExist:
                print('Quay not found, skipping %s' % file)
            except ServiceJourney.DoesNotExist:
                print('ServiceJourney not found, skipping %s' % file)
            # break
            # self.load_routes_and_point_on_route(root)
