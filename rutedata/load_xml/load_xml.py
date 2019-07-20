import datetime
import io
import xml.etree.ElementTree
import xml.etree.ElementTree
import zipfile
from datetime import datetime

import requests


class LoadXml:
    namespaces = {'netex': 'http://www.netex.org.uk/netex'}

    @staticmethod
    def load_file(url):
        response = requests.get(url)
        zip_bytes = io.BytesIO(response.content)
        zip_file = zipfile.ZipFile(zip_bytes)
        return zip_file

    def load_netex(self, file='_RUT_shared_data.xml'):
        url = 'https://storage.googleapis.com/marduk-production/outbound/netex/rb_rut-aggregated-netex.zip'
        zip_file = self.load_file(url)
        if file:
            xml_bytes = zip_file.read(file)
            return xml.etree.ElementTree.fromstring(xml_bytes)
        else:
            return zip_file

    def load_tiamat(self):
        url = 'https://storage.googleapis.com/marduk-production/tiamat/Oslo_og_Akershus_latest.zip'
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


