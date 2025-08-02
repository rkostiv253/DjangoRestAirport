from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from airport.models import (
    Country,
    City,
    Airport,
    CrewMember,
    AirplaneType,
    Airplane,
    Route,
    Flight,
    Order,
    Ticket,
)


class CountrySerializer(serializers.ModelSerializer):

    class Meta:
        model = Country
        fields = ("id", "name")


class CitySerializer(serializers.ModelSerializer):

    class Meta:
        model = City
        fields = ("id", "city", "country")


class CityListSerializer(CitySerializer):
    country = serializers.SlugRelatedField(
        many=False,
        read_only=True,
        slug_field="name",
    )

    class Meta:
        model = City
        fields = ("id", "city", "country")


class AirportSerializer(serializers.ModelSerializer):

    class Meta:
        model = Airport
        fields = ("id", "name", "city")


class AirportListSerializer(AirportSerializer):
    city = serializers.SlugRelatedField(
        many=False,
        read_only=True,
        slug_field="city"
    )
    country = serializers.CharField(source="city.country.name", read_only=True)

    class Meta:
        model = Airport
        fields = ("id", "name", "city", "country")


class AirportDetailSerializer(AirportSerializer):
    city = CityListSerializer(many=False, read_only=True)

    class Meta:
        model = Airport
        fields = ("id", "name", "city")


class CrewMemberSerializer(serializers.ModelSerializer):

    class Meta:
        model = CrewMember
        fields = ("id", "first_name", "last_name", "full_name")


class AirplaneTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = AirplaneType
        fields = ("id", "name")


class AirplaneSerializer(serializers.ModelSerializer):

    class Meta:
        model = Airplane
        fields = (
            "id",
            "name",
            "rows",
            "seats_in_row",
            "airplane_type",
            "capacity"
        )


class AirplaneListSerializer(AirplaneSerializer):
    airplane_type = serializers.SlugRelatedField(
        many=False, read_only=True, slug_field="name"
    )

    class Meta:
        model = Airplane
        fields = (
            "id",
            "name",
            "rows",
            "seats_in_row",
            "airplane_type",
            "capacity"
        )


class AirplaneDetailSerializer(AirplaneSerializer):
    airplane_type = AirplaneTypeSerializer(many=False, read_only=True)

    class Meta:
        model = Airplane
        fields = (
            "id",
            "name",
            "rows",
            "seats_in_row",
            "airplane_type",
            "capacity"
        )


class RouteSerializer(serializers.ModelSerializer):

    class Meta:
        model = Route
        fields = ("id", "departure_airport", "destination", "distance")


class RouteImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Route
        fields = ("id", "image")


class RouteListSerializer(RouteSerializer):
    departure_airport = serializers.SlugRelatedField(
        many=False, read_only=True, slug_field="name"
    )

    destination = serializers.SlugRelatedField(
        many=False, read_only=True, slug_field="name"
    )

    class Meta:
        model = Route
        fields = (
            "id",
            "departure_airport",
            "destination",
            "distance",
            "image"
        )


class RouteDetailSerializer(RouteSerializer):
    departure_airport = AirportListSerializer(many=False, read_only=True)
    destination = AirportListSerializer(many=False, read_only=True)

    class Meta:
        model = Route
        fields = (
            "id",
            "departure_airport",
            "destination",
            "distance",
            "image"
        )


class FlightSerializer(serializers.ModelSerializer):

    def validate(self, attrs):
        departure_time = attrs.get("departure_time")
        arrival_time = attrs.get("arrival_time")
        now = timezone.now()

        if departure_time and arrival_time:
            if departure_time < now or arrival_time < now:
                raise serializers.ValidationError(
                    "Departure time and arrival time can't be in the past"
                )

            if departure_time > arrival_time:
                raise serializers.ValidationError(
                    "Departure time can't be later than arrival time"
                )

        return attrs

    class Meta:
        model = Flight
        fields = (
            "id",
            "route",
            "airplane",
            "departure_time",
            "arrival_time",
            "crew"
        )


class FlightListSerializer(FlightSerializer):
    departure = serializers.CharField(
        source="route.departure_airport",
        read_only=True
    )
    destination = serializers.CharField(
        source="route.destination",
        read_only=True
    )
    airplane = serializers.CharField(
        source="airplane.name",
        read_only=True
    )
    crew = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field="full_name"
    )
    total_seats = serializers.IntegerField(
        source="airplane.capacity",
        read_only=True
    )
    tickets_available = serializers.IntegerField(read_only=True)
    route_image = serializers.ImageField(source="route.image", read_only=True)

    class Meta:
        model = Flight
        fields = (
            "id",
            "departure",
            "destination",
            "airplane",
            "departure_time",
            "arrival_time",
            "crew",
            "total_seats",
            "tickets_available",
            "route_image",
        )


class TicketSerializer(serializers.ModelSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)

        flight = attrs.get("flight")
        if isinstance(flight, int):
            flight = Flight.objects.filter(id=flight).first()

        if not flight:
            raise serializers.ValidationError(
                {"flight": "Invalid flight specified."}
            )

        Ticket.validate_ticket(
            attrs["row"],
            attrs["seat"],
            flight.airplane,
            serializers.ValidationError,
        )

        return data

    class Meta:
        model = Ticket
        fields = ("id", "row", "seat", "flight")


class TicketListSerializer(TicketSerializer):
    flight = FlightListSerializer(many=False, read_only=True)


class TicketSeatsSerializer(TicketSerializer):
    class Meta:
        model = Ticket
        fields = ("row", "seat")


class FlightDetailSerializer(FlightSerializer):
    route = RouteDetailSerializer(many=False, read_only=True)
    airplane = AirplaneDetailSerializer(
        many=False,
        read_only=True
    )
    crew = CrewMemberSerializer(many=True, read_only=True)
    taken_places = TicketSeatsSerializer(
        source="tickets",
        many=True, read_only=True
    )

    class Meta:
        model = Flight
        fields = (
            "id",
            "route",
            "airplane",
            "departure_time",
            "arrival_time",
            "crew",
            "taken_places",
        )


class OrderSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(many=True, read_only=False, allow_empty=False)

    class Meta:
        model = Order
        fields = ("id", "tickets", "created_at")

    def create(self, validated_data):
        with transaction.atomic():
            tickets_data = validated_data.pop("tickets")
            order = Order.objects.create(**validated_data)
            for ticket_data in tickets_data:
                Ticket.objects.create(order=order, **ticket_data)
            return order


class OrderListSerializer(OrderSerializer):
    tickets = TicketListSerializer(many=True, read_only=True)
