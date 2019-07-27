import re
import xml

from .load_xml import LoadXml


class LinePassingHelper(LoadXml):
    def __init__(self, line_id, service_journey_id):
        [file_name, file] = self.find_line_file(line_id=line_id)
        self.root = xml.etree.ElementTree.fromstring(file)
        self.passings = self.find_passings(service_journey_id,
                                           xml_root=self.root)

    def get_quay(self, passing):
        stop_point_id = self.get(passing, 'StopPointInJourneyPatternRef')
        point_id = self.stop_point(stop_point_id=stop_point_id,
                                   xml_root=self.root)
        quay_id = re.sub(r'default-([0-9])', r'NSR:Quay:\1', point_id)
        return quay_id

    def first_passing(self):
        return self.passings[0]

    def last_passing(self):
        return self.passings[-1]

    def first_quay(self):
        return self.get_quay(self.first_passing())

    def last_quay(self):
        return self.get_quay(self.last_passing())
