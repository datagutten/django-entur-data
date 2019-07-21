import re
import xml.etree.ElementTree

from rutedata.models import Line, PassingTime, PointOnRoute, Quay, Route, ServiceJourney
from .load_xml import LoadXml


class LoadLines(LoadXml):
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
                print('Quay %s does not exist' % quay_id)
                raise e

            point_db = PointOnRoute(
                id=point.attrib['id'],
                Route=route_db,
                order=point.attrib['order'],
                quay=quay,
            )
            point_db.save()

    def journey_pattern(self, line_root, journey_id):
        return line_root.find(
            './/netex:journeyPatterns/netex:JourneyPattern[@id="%s"]' % journey_id,
            self.namespaces)

    def load_service_journeys(self, root, output=False):
        """
        Load ServiceJourney
        Requires Line, Route
        :param root:
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
        for journey in journeys:
            if output:
                print('Loading %d of %d' % (count, total), end='\r')
            count += 1
            journey_id = journey.get('id')
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

            journey_pattern = self.journey_pattern(
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
            self.load_passings(journey, journey_db)
        if output:
            print("")
        self.cleanup_journeys(lines, valid_journeys)

    @staticmethod
    def cleanup_journeys(lines, valid_journeys):
        for line in lines:
            for journey in ServiceJourney.objects.filter(line=line):
                if journey.id not in valid_journeys:
                    print('Invalid journey: %s' % journey.id)
                    journey.delete()

    def load_passings(self, journey, journey_db=None):
        """
        Load PassingTime
        Called in loop by load_service_journeys
        Requires PointOnRoute
        :param xml.etree.ElementTree.Element journey:
        :param ServiceJourney journey_db:
        :return:
        """

        passings = journey.findall(
            './/netex:passingTimes/netex:TimetabledPassingTime',
            self.namespaces)
        if journey_db is None:
            journey_db = ServiceJourney.objects.get(id=journey.get('id'))

        if not passings:
            raise ValueError('No passings found')

        for timetabled_passing_time in passings:
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
                raise e

            passing = PassingTime(id=journey_id,
                                  service_journey=journey_db,
                                  point=point,
                                  )

            departure = timetabled_passing_time.find('netex:DepartureTime', self.namespaces)
            if departure is not None:
                passing.departure_time = self.parse_time(departure.text)
            arrival = timetabled_passing_time.find('netex:ArrivalTime', self.namespaces)
            if arrival is not None:
                passing.arrival_time = self.parse_time(arrival.text)

            passing.save()

    def load_lines(self, line_filter=None, load_lines=True, load_routes=True, load_service_journeys=True, output=False):
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
            if load_lines:
                self.load_line(root)
            if load_routes:
                self.load_route(root)
            if load_service_journeys:
                self.load_service_journeys(root, output)
            # break
            # self.load_routes_and_point_on_route(root)
