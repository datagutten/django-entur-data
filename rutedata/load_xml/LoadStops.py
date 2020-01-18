from django.db.utils import IntegrityError

from rutedata.models import GroupOfStopPlaces, Quay, Stop
from .load_xml import LoadXml


class LoadStops(LoadXml):
    def __init__(self, file=None):
        self.root = self.load_tiamat(file)
        self.topographic_places = self.root.find(
            './netex:dataObjects/netex:SiteFrame/netex:topographicPlaces',
            self.namespaces)

    def topographic_place(self, topographic_place_ref):
        """return self.topographic_places.find(
            './netex:TopographicPlace[@id="%s"]/netex:Descriptor/netex:Name' %
            topographic_place_ref,
            self.namespaces).text"""

        return self.text(
            self.topographic_places,
            'TopographicPlace[@id="%s"]/netex:Descriptor/netex:Name' %
            topographic_place_ref)

    def child_stops(self, stop_id):
        return self.root.findall(
            './netex:dataObjects/netex:SiteFrame/netex:stopPlaces/netex:StopPlace/netex:ParentSiteRef[@ref="%s"]/..' %
            stop_id, self.namespaces)
        # NSR:StopPlace:58191

    def is_parent(self, stop):
        parent = self.text(
            stop,
            'keyList/netex:KeyValue/netex:Key[.="IS_PARENT_STOP_PLACE"]/../netex:Value')
        if parent == 'true':
            return True
        elif parent == 'false':
            return False
        else:
            raise ValueError('Invalid value for IS_PARENT_STOP_PLACE: %s' %
                             parent)

    def load_stops(self, filter_stop_id=None):
        """
        Load Stop and Quay
        :return:
        """
        stops = self.root.find(
            './netex:dataObjects/netex:SiteFrame/netex:stopPlaces',
            self.namespaces)

        for stop in stops:
            stop_id = stop.get('id')
            if filter_stop_id and not filter_stop_id == stop_id:
                continue
            stop_db = Stop(id=stop_id)
            try:
                stop_db.Name = self.text(stop, 'Name')
                stop_db.Description = self.text(stop, 'Description')
                [stop_db.latitude, stop_db.longitude] = self.coordinates(stop)

                adjacent = self.text(stop, 'netex:adjacentSites/netex:SiteRef')
                if adjacent is not None:
                    try:
                        stop_db.adjacent = Stop.objects.get(id=adjacent)
                    except Stop.DoesNotExist:
                        print('Missing adjacent stop %s' % adjacent)

                stop_db.TransportMode = self.text(stop, 'TransportMode')
                try:
                    stop_db.Zone = stop.find(
                        './netex:tariffZones/netex:TariffZoneRef',
                        self.namespaces).get('ref')
                except AttributeError:
                    pass

                topographic_place_ref = stop.find('netex:TopographicPlaceRef',
                                                  self.namespaces).get('ref')
                stop_db.TopographicPlace = \
                    self.topographic_place(topographic_place_ref)

            except ValueError as e:
                print('Feil på %s: %s' % (stop_db, e))
                raise e
            try:
                stop_db.save()
            except IntegrityError as e:
                print('Feil ved lagring av %s: %s' % (stop_db, e))
                print(stop_db.Name, stop_db.latitude, stop_db.longitude)
                raise e

            """if self.is_parent(stop):
                print('%s is a parent stop' % stop_id)
                for child in self.child_stops(stop_id):
                    child_db = Stop.objects.get(id=child.get('id'))
                    child_db.Parent = stop_db
                    child_db.save()"""

            self.load_quays(stop, stop_db)
        self.load_child_stops()

    def load_child_stops(self):
        """
        Update stops with children
        All stops must be loaded
        :return:
        """
        stops = self.root.find(
            './netex:dataObjects/netex:SiteFrame/netex:stopPlaces',
            self.namespaces)

        for stop in stops:
            parent = stop.find('netex:ParentSiteRef', self.namespaces)
            if parent is not None:
                stop_db = Stop.objects.get(id=stop.get('id'))
                parent = parent.get('ref')
                try:
                    stop_db.Parent = Stop.objects.get(id=parent)
                    stop_db.save()
                except Stop.DoesNotExist as e:
                    print('Parent stop %s not found' % parent)
                    raise e

    def load_quays(self, stop, stop_db):
        """
        Load Quay
        Called in loop by load_stop()
        :param stop:
        :param stop_db:
        :return:
        """
        quays = stop.findall('./netex:quays/netex:Quay', self.namespaces)
        for quay in quays:
            ImportedId = self.text(
                quay,
                'keyList/netex:KeyValue[netex:Key="imported-id"]/netex:Value'
            )

            quay_db = Quay(
                id=quay.attrib['id'],
                Stop=stop_db,
                ImportedId=ImportedId,
            )

            description = quay.find('netex:Description', self.namespaces)
            if description is not None:
                quay_db.Description = description.text
            public_code = quay.find('netex:PublicCode', self.namespaces)
            if public_code is not None:
                quay_db.PublicCode = public_code.text

            [quay_db.latitude, quay_db.longitude] = self.coordinates(quay)

            quay_db.save()

    def load_groups(self):
        for group in self.root.find(
                './netex:dataObjects/netex:SiteFrame/netex:groupsOfStopPlaces',
                self.namespaces):
            group_db = GroupOfStopPlaces(id=group.get('id'))
            group_db.name = group.find('netex:Name', self.namespaces).text
            [group_db.latitude, group_db.longitude] = self.coordinates(group)
            group_db.save()
            for member in group.find('netex:members', self.namespaces):
                try:
                    stop = Stop.objects.get(id=member.get('ref'))
                    # print('%s is member of %s' % (stop, group_db))
                    group_db.members.add(stop)
                except Stop.DoesNotExist:
                    print('Stop %s member of %s not found' % (member.get('ref'), group_db))
