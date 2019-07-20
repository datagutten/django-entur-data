from django.urls import path

from . import views

app_name = 'rutedata'
urlpatterns = [
    path('stops/route/<str:route_id>.kml', views.stop_list,
         name='route_stops'),
    path('lines/<str:stop>', views.lines_from_stop,
         name='lines_from_stop'),
    path('routes/<str:line>', views.routes_for_line,
         name='routes_for_line'),
    path('journeys/<str:route>', views.journeys_for_route,
         name='journeys_for route')
]
