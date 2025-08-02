from django.contrib import admin

from airport.models import (
    Country,
    City,
    Airport,
    CrewMember,
    AirplaneType,
    Airplane,
    Route,
    Flight,
    Ticket,
    Order,
)

admin.site.register(Country)
admin.site.register(City)
admin.site.register(Airport)
admin.site.register(CrewMember)
admin.site.register(AirplaneType)
admin.site.register(Airplane)
admin.site.register(Route)
admin.site.register(Flight)
admin.site.register(Ticket)
admin.site.register(Order)
