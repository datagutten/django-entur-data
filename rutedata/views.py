from django.shortcuts import render
from .models import Route, Stop, PointOnRoute, ServiceJourney


def stop_list(request, route_id):
    route = Route.objects.get(id=route_id)
    points = PointOnRoute.objects.filter(RouteId=route)
    context = {
        'points': points,
    }
    return render(request, 'rutedata/stops_kml.html', context)


def lines_from_stop(request, stop):
    print(stop)
    stop_obj = Stop.objects.get(id=stop)
    lines = stop_obj.lines()
    return render(request, 'rutedata/lines.html', {'lines': lines})


def routes_for_line(request, line):
    routes = Route.objects.filter(LineRef__id=line)
    return render(request, 'rutedata/routes.html', {'routes': routes})


def journeys_for_route(request, route):
    journeys = ServiceJourney.objects.filter(route=route)
    return render(request, 'rutedata/service_journey.html',
                  {'journeys': journeys})
