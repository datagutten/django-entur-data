from django.contrib import admin

from .models import GroupOfStopPlaces, Line, PassingTime, PointOnRoute, Quay, Route, ServiceJourney, Stop

"""class StopPointInline(admin.TabularInline):
    model = StopPoint
    readonly_fields = ('id', 'name')
    extra = 0

    def has_add_permission(self, request, obj):
        return False"""


class ParentStopInline(admin.TabularInline):
    model = Stop
    fk_name = 'Parent'
    readonly_fields = ('id', 'Name', 'Description', 'latitude', 'longitude',
                       'Zone', 'TransportMode', 'TopographicPlace', 'Adjacent')
    extra = 0

    def has_add_permission(self, request, obj):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class QuayInline(admin.TabularInline):
    model = Quay
    # readonly_fields = ('id', 'name')
    extra = 0

    def has_add_permission(self, request, obj):
        return False


class StopAdmin(admin.ModelAdmin):
    list_display = ('Name', 'TransportMode', 'TopographicPlace')
    list_filter = ('TopographicPlace', 'Zone')
    inlines = (QuayInline, ParentStopInline)
    readonly_fields = ('Adjacent',)


admin.site.register(Stop, StopAdmin)


class QuayAdmin(admin.ModelAdmin):
    list_display = ('Stop', 'Description', 'latitude', 'longitude',
                    'id')
    list_filter = ('Stop__TopographicPlace', 'Stop__TransportMode')


admin.site.register(Quay, QuayAdmin)


admin.site.register(Line)


class RouteAdmin(admin.ModelAdmin):
    list_display = ('id', 'Name', 'ShortName', 'LineRef')
    list_filter = ('LineRef__PublicCode',)


admin.site.register(Route, RouteAdmin)
# admin.site.register(StopPoint)


class PointOnRouteAdmin(admin.ModelAdmin):
    # list_filter = ('Route__Line__PublicCode', 'RouteId')
    pass


admin.site.register(PointOnRoute, PointOnRouteAdmin)
admin.site.register(GroupOfStopPlaces)


class ServiceJourneyAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'line', 'route', 'private_code')
    list_filter = ('line', 'route')


admin.site.register(ServiceJourney, ServiceJourneyAdmin)


class PassingTimeAdmin(admin.ModelAdmin):
    list_display = ('service_journey', 'point', 'departure_time',
                    'arrival_time', 'time')
    list_filter = ('service_journey__line', 'point__quay', 'service_journey')


admin.site.register(PassingTime, PassingTimeAdmin)
