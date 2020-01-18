import datetime
import io
import os
import re
import xml.etree.ElementTree
import xml.etree.ElementTree
import zipfile
from datetime import datetime

import requests


def parse_line_id(line_id):
    # RUT:Line:83
    matches = re.match(r'([A-Z]+):Line:([0-9A-Z]+)', line_id)
    return matches

class LoadXml:
    namespaces = {'netex': 'http://www.netex.org.uk/netex'}

    @staticmethod
    def load_file(url):
        local_file = '%s/zip/%s' % (os.path.dirname(__file__), os.path.basename(url))
        if not os.path.exists(local_file):
            response = requests.get(url)
            response.raise_for_status()
            zip_bytes = io.BytesIO(response.content)
        else:
            zip_bytes = local_file
        zip_file = zipfile.ZipFile(zip_bytes)
        return zip_file

    def load_netex(self, file='_RUT_shared_data.xml', district='rut'):
        """

        :param str|none file:
        :param district:
        :return:
        """
        url = 'https://storage.googleapis.com/marduk-production/outbound/netex/rb_%s-aggregated-netex.zip' % district
        zip_file = self.load_file(url)
        if file:
            xml_bytes = zip_file.read(file)
            return xml.etree.ElementTree.fromstring(xml_bytes)
        else:
            return zip_file

    def find_line_file(self, line_num=None, line_id=None, region='RUT'):

        if line_id is None:
            wanted_file = '{0}_{0}-Line-{1}'.format(region, line_num)
        else:
            matches = parse_line_id(line_id)
            wanted_file = '{0}_{0}-Line-{1}'.format(matches.group(1),
                                                    matches.group(2))
        zip_file = self.load_netex(file=None)
        for file in zip_file.namelist():
            if file.find(wanted_file) > -1:
                return [file, zip_file.read(file)]

    def find_line_num(self, service_journey_id):
        matches = re.match(r'([A-Z]+):ServiceJourney:([0-9A-Z]+)-.+', service_journey_id)
        region = matches.group(1)
        line = matches.group(2)
        return [region, line]

    def find_service_journey(self, service_journey_id, line=None, region=None, xml_root=None):
        if xml_root is None:
            if line is None:
                matches = re.match(r'([A-Z]+):ServiceJourney:([0-9A-Z]+)-.+', service_journey_id)
                if not region:
                    region = matches.group(1)
                line = matches.group(2)
            [file_name, file] = self.find_line_file(line, region)
            root = xml.etree.ElementTree.fromstring(file)
        else:
            root = xml_root
        journey = root.find('.//netex:ServiceJourney[@id="%s"]' %
                            service_journey_id, self.namespaces)
        return journey

    def find_passings(self, service_journey_id, line=None, region=None, xml_root=None):
        journey = self.find_service_journey(service_journey_id, line, region, xml_root=xml_root)
        return journey.findall('.//netex:TimetabledPassingTime', self.namespaces)

    def stop_point(self, line_id=None, stop_point_id=None, xml_root=None):
        if xml_root is None:
            [file_name, file] = self.find_line_file(line_id=line_id)
            root = xml.etree.ElementTree.fromstring(file)
        else:
            root = xml_root
        point = root.find('.//netex:StopPointInJourneyPattern[@id="%s"]' % stop_point_id, self.namespaces)
        return self.get(point, 'ScheduledStopPointRef')

    def load_tiamat(self, file=None):
        if not file:
            file = '03_Oslo_latest.zip'
        url = 'https://storage.googleapis.com/marduk-production/tiamat/%s' % file
        zip_file = self.load_file(url)
        xml_file = zip_file.namelist()[0]
        xml_bytes = zip_file.read(xml_file)
        return xml.etree.ElementTree.fromstring(xml_bytes)

    def text(self, item, query):
        match = item.find('netex:%s' % query, self.namespaces)
        if match is not None:
            return match.text
        else:
            return None

    def get(self, item, query, attribute='ref'):
        match = item.find('netex:%s' % query, self.namespaces)
        if match is not None:
            return match.get(attribute)
        else:
            return None

    def coordinates(self, item):
        lat = float(item.find('netex:Centroid/netex:Location/netex:Latitude',
                              self.namespaces).text)
        lon = float(item.find('netex:Centroid/netex:Location/netex:Longitude',
                              self.namespaces).text)
        return [lat, lon]

    @staticmethod
    def parse_time(time):
        return datetime.strptime(time, '%H:%M:%S')


