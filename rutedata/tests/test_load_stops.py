from django.test import TestCase
from rutedata.load_xml.LoadStops import LoadStops
from rutedata.models import Stop


class LoadStopsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        load = LoadStops('03_Oslo_latest.zip')
        load.load_stops()

    def test_topographic_place(self):
        load = LoadStops('03_Oslo_latest.zip')
        self.assertIsNotNone(load.topographic_places)
        name = load.topographic_place('KVE:TopographicPlace:0301')
        self.assertEqual('Oslo', name)

    def test_child_stops(self):
        """
        6031 and 6029 should be children of 58191
        :return:
        """
        child1 = Stop.objects.get(id='NSR:StopPlace:6031')
        child2 = Stop.objects.get(id='NSR:StopPlace:6029')
        self.assertIsNotNone(child1.Parent)
        parent_stop = Stop.objects.get(id='NSR:StopPlace:58191')
        self.assertEqual(child1.Parent, parent_stop)
        # print(parent_stop.children.all())
        self.assertIn(child1, parent_stop.children.all())
        self.assertIn(child2, parent_stop.children.all())
