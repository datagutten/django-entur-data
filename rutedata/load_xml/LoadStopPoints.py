import re

# noinspection PyUnresolvedReferences
from rutedata.models import Quay, StopPoint
from .load_xml import LoadXml


class LoadStopPoints(LoadXml):
    def load_stop_points(self):
        """
        Load StopPoint
        Quay must be loaded before this
        :return:
        """
        return
        root = self.load_netex()
        for point in root.findall('.//netex:scheduledStopPoints/netex:ScheduledStopPoint', self.namespaces):
            id_string = point.attrib['id']
            point_id = (re.search(r'[A-Z]+:ScheduledStopPoint:([A-Za-z0-9\-]+)', id_string))
            point_id = point_id[1]
            quay = root.find(
                './/netex:PassengerStopAssignment/netex:ScheduledStopPointRef[@ref="%s"]/../netex:QuayRef' % id_string,
                self.namespaces)
            quay = quay.attrib['ref']
            try:
                stop_details = Quay.objects.get(PrefixedId=quay)
                point_db = StopPoint(
                    id=point_id,
                    # name=point.find('netex:Name', self.namespaces).text,
                    name=self.text(point, 'Name'),
                    QuayRef=stop_details
                )
                point_db.save()
            except Quay.DoesNotExist:
                print('Quay not found: %s' % quay)
                return
