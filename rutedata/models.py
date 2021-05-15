from django.db import models


class Stop(models.Model):
    id = models.CharField(max_length=30, primary_key=True)
    Name = models.CharField(max_length=200)
    Description = models.CharField(max_length=200, blank=True, null=True)
    latitude = models.DecimalField(max_digits=11, decimal_places=8)
    longitude = models.DecimalField(max_digits=11, decimal_places=8)
    Zone = models.CharField('Sone', max_length=20, blank=True, null=True)
    TransportMode = models.CharField(max_length=200, blank=True, null=True)
    TopographicPlace = models.CharField(max_length=200, blank=True, null=True)
    Parent = models.ForeignKey('self', on_delete=models.SET_NULL, blank=True,
                               null=True, related_name='children')
    Adjacent = models.ForeignKey('self', on_delete=models.SET_NULL, blank=True,
                                 null=True, related_name='adjacent')

    def __str__(self):
        return '%s [%s] (%s)' % (self.Name, self.TransportMode,
                                 self.TopographicPlace)

    class Meta:
        ordering = ['Name']

    # Get lines departing from stop
    def lines(self):
        lines = []
        points = PointOnRoute.objects.filter(quay__Stop=self)
        for point in points:
            line = point.RouteId.LineRef
            if line not in lines:
                lines.append(line)
        return lines


class Line(models.Model):
    id = models.CharField(max_length=20, primary_key=True)
    Name = models.CharField(max_length=200, blank=True, null=True)
    TransportMode = models.CharField(max_length=200, blank=True, null=True)
    TransportSubmode = models.CharField(max_length=200, blank=True, null=True)
    PublicCode = models.CharField('Linjenummer', max_length=200,
                                  blank=True, null=True)
    OperatorRef = models.CharField('Operatør', max_length=200,
                                   blank=True, null=True)
    RepresentedByGroupRef = models.CharField(max_length=200,
                                             blank=True, null=True)
    Colour = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return '%s %s' % (self.PublicCode, self.Name)


class Quay(models.Model):
    id = models.CharField(max_length=20, primary_key=True)
    Stop = models.ForeignKey(Stop, on_delete=models.CASCADE,
                             related_name='quays', blank=True, null=True)
    ImportedId = models.CharField(max_length=200, blank=True, null=True)
    latitude = models.DecimalField(max_digits=11, decimal_places=8, blank=True, null=True)
    longitude = models.DecimalField(max_digits=11, decimal_places=8, blank=True, null=True)
    PublicCode = models.CharField(max_length=20, blank=True, null=True)
    Description = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return '%s (%s)' % (self.Stop.Name, self.id)

    class Meta:
        ordering = ['Stop__Name']

    def remove_prefix(self):
        import re
        return re.sub(r'[A-Z]+:Quay:([0-9]+)', r'\1', self.id)


class Route(models.Model):
    id = models.CharField(max_length=20, primary_key=True)
    Name = models.CharField(max_length=200, blank=True, null=True)
    ShortName = models.CharField(max_length=200, blank=True, null=True)
    LineRef = models.ForeignKey(Line, on_delete=models.CASCADE)
    origin = models.ForeignKey(Quay, on_delete=models.CASCADE,
                               related_name='route_origin',
                               blank=True, null=True)
    destination = models.ForeignKey(Quay, on_delete=models.CASCADE,
                                    related_name='route_destination',
                                    blank=True, null=True)

    def __str__(self):
        return '%s %s' % (self.id, self.Name)


class PointOnRoute(models.Model):
    id = models.CharField(max_length=30, primary_key=True)
    Route = models.ForeignKey(Route, on_delete=models.CASCADE)
    order = models.IntegerField('Rekkefølge')
    # StopPoint = models.ForeignKey(StopPoint, on_delete=models.CASCADE,
    #                              )
    quay = models.ForeignKey(Quay, on_delete=models.CASCADE,
                             null=True, blank=True)

    def __str__(self):
        return '%s: holdeplass %s %s' % (self.Route.id, self.order,
                                         self.quay.Stop.Name)

    def first_stop(self):
        return self.objects.get(order=1)

    def last_stop(self):
        return PassingTime.objects.filter(service_journey=self).\
            latest('point__order')


class GroupOfStopPlaces(models.Model):
    id = models.CharField(max_length=30, primary_key=True)
    name = models.CharField(max_length=200)
    members = models.ManyToManyField(Stop, related_name='groups')
    latitude = models.DecimalField(max_digits=11, decimal_places=8)
    longitude = models.DecimalField(max_digits=11, decimal_places=8)

    def __str__(self):
        return '%s %s' % (self.id, self.name)


class ServiceJourney(models.Model):
    id = models.CharField(max_length=50, primary_key=True)
    name = models.CharField(max_length=100)
    private_code = models.CharField(max_length=8)
    line = models.ForeignKey(Line, on_delete=models.CASCADE, db_index=True)
    route = models.ForeignKey(Route, on_delete=models.CASCADE)

    def passings(self):
        return PassingTime.objects.filter(service_journey=self)
    # RUT:ServiceJourney:83-509

    def first_passing(self):
        return PassingTime.objects.get(service_journey=self,
                                       point__order=1)

    def last_passing(self):
        return PassingTime.objects.filter(service_journey=self).\
            latest('point__order')

    def private_id(self):
        from re import sub
        key = sub(r'([A-Za-z:]+[0-9]+).+', r'\1', self.id)
        return '%s-%s' % (key, self.private_code)


class PassingTime(models.Model):
    id = models.CharField(max_length=60, primary_key=True)
    service_journey = models.ForeignKey(ServiceJourney,
                                        on_delete=models.CASCADE,
                                        db_index=True)
    point = models.ForeignKey(PointOnRoute, on_delete=models.CASCADE)
    departure_time = models.TimeField(null=True, blank=True)
    arrival_time = models.TimeField(null=True, blank=True)
    line = models.ForeignKey(Line, on_delete=models.CASCADE,
                             db_index=True, blank=True, null=True)

    def time(self):
        if self.departure_time:
            return self.departure_time.strftime('%H:%M')
        elif self.arrival_time:
            return self.arrival_time.strftime('%H:%M')

    def __str__(self):
        return '%s %s %s' % (self.point, self.arrival_time,
                             self.departure_time)


"""class Operator(models.Model):
    id = models.CharField(max_length=60, primary_key=True)
    name = models.CharField(max_length=200)"""