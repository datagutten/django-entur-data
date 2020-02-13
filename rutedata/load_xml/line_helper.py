from .load_xml import LoadXml


class LineHelper(LoadXml):

    def journey_pattern(self, line_root, journey_id):
        return line_root.find(
            './/netex:journeyPatterns/netex:JourneyPattern[@id="%s"]' % journey_id,
            self.namespaces)

    def vehicle_journeys(self, line_root):
        """

        :param xml.etree.ElementTree.Element line_root:
        :return:
        """
        return line_root.findall(
            './/netex:frames/netex:TimetableFrame/netex:vehicleJourneys/netex:ServiceJourney', self.namespaces)

    def days(self, day_type_ref):
        root = self.load_netex()
        day_type = root.find('.//netex:DayType[@id="%s"]' % day_type_ref, self.namespaces)
        print(day_type)
        print(day_type.findall('./netex:properties', self.namespaces))

    def passings(self, service_journey, line):
        self.find_line_file()
        root = self.load_netex()
        journey = root.find('.//netex:ServiceJourney[@id="%s"]' % service_journey, self.namespaces)
        print(journey)
