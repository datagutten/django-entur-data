from django.test import TestCase
from rutedata.load_xml.LoadLines import LoadLines
from rutedata.load_xml.LoadStops import LoadStops
from rutedata.models import Line, Stop


class LoadStopsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # super().__init__(method_name)
        load_stops = LoadStops('30_Viken_latest.zip')
        load_stops.load_stops()
        load_stops = LoadStops('03_Oslo_latest.zip')
        load_stops.load_stops()

        load = LoadLines()
        load.load_lines('RUT_RUT-Line-83', load_service_journeys=False)

    def test_get_line(self):
        line = Line.objects.get(id='RUT:Line:83')
        self.assertEqual('83', line.PublicCode)

    def test_line_color(self):
        line = Line.objects.get(id='RUT:Line:83')
        self.assertEqual('E60000', line.Colour)

