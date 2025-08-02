from datetime import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status
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
from airport.serializers import FlightDetailSerializer, FlightListSerializer

FLIGHT_URL = reverse("airport:flight-list")
ROUTE_URL = reverse("airport:route-list")


def sample_departure_country(**params):
    defaults = {
        "name": "USA",
    }
    defaults.update(params)
    return Country.objects.get_or_create(**defaults)[0]


def sample_departure_city(
    **params,
):
    defaults = {
        "city": "New York",
        "country": sample_departure_country(),
    }
    defaults.update(params)
    return City.objects.get_or_create(**defaults)[0]


def sample_departure_airport(**params):
    defaults = {
        "name": "JFK Airport",
        "city": sample_departure_city(),
    }
    defaults.update(params)
    return Airport.objects.get_or_create(**defaults)[0]


def sample_destination_country(**params):
    defaults = {
        "name": "United Kingdom",
    }
    defaults.update(params)
    return Country.objects.get_or_create(**defaults)[0]


def sample_destination_city(
    **params,
):
    defaults = {
        "city": "London",
        "country": sample_destination_country(),
    }
    defaults.update(params)
    return City.objects.get_or_create(**defaults)[0]


def sample_destination(**params):
    defaults = {
        "name": "Heathrow Airport",
        "city": sample_destination_city(),
    }
    defaults.update(params)
    return Airport.objects.get_or_create(**defaults)[0]


def sample_airplane_type(**params):
    defaults = {
        "name": "Boeing 787",
    }
    defaults.update(params)
    return AirplaneType.objects.get_or_create(**defaults)[0]


def sample_airplane(**params):
    defaults = {
        "name": "AB-850",
        "rows": 30,
        "seats_in_row": 6,
        "airplane_type": sample_airplane_type(),
    }
    defaults.update(params)
    return Airplane.objects.create(**defaults)


def sample_route(**params):
    defaults = {
        "distance": 5567,
        "departure_airport": sample_departure_airport(),
        "destination": sample_destination(),
    }
    defaults.update(params)
    return Route.objects.create(**defaults)


def sample_flight(**params):
    crew_member1 = CrewMember.objects.create(first_name="John", last_name="Smith")
    crew_member2 = CrewMember.objects.create(first_name="Paul", last_name="Richards")
    defaults = {
        "route": sample_route(),
        "airplane": sample_airplane(),
        "departure_time": datetime(
            year=2026, month=6, day=15, hour=15, minute=00, second=00
        ),
        "arrival_time": datetime(
            year=2026, month=6, day=15, hour=17, minute=00, second=00
        ),
    }
    defaults.update(params)
    flight = Flight.objects.create(**defaults)
    flight.crew.set([crew_member1, crew_member2])

    return flight


def sample_order(user):
    return Order.objects.create(user=user)


def sample_ticket(order, flight, **params):
    defaults = {"row": 15, "seat": 2, "flight": flight, "order": order}
    defaults.update(params)
    return Ticket.objects.create(**defaults)


def detail_url(flight_id):
    return reverse("airport:flight-detail", args=[flight_id])


class UnauthenticatedFlightApiTests(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        response = self.client.get(FLIGHT_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedFlightApiTest(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@test.com",
            password="test123",
        )

        self.client.force_authenticate(user=self.user)
        self.flight = sample_flight()
        self.order = sample_order(user=self.user)
        sample_ticket(self.order, flight=self.flight)
        self.route = self.flight.route
        self.airplane = self.flight.airplane
        tickets = Ticket.objects.filter(flight=self.flight)
        self.flight.tickets_available = (
            self.airplane.rows * self.airplane.seats_in_row
        ) - tickets.count()
        self.flight.save()

    def test_get_flights(self):
        flights = self.client.get(FLIGHT_URL)
        self.assertEqual(flights.status_code, status.HTTP_200_OK)

    def test_retrieve_flight(self):
        url = detail_url(self.flight.id)
        response = self.client.get(url)

        serializer = FlightDetailSerializer(self.flight)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_create_flight_forbidden(self):
        crew_member1 = CrewMember.objects.create(first_name="John", last_name="Doe")
        payload = {
            "route": self.route.id,
            "airplane": self.airplane.id,
            "departure_time": datetime(
                year=2026, month=6, day=15, hour=15, minute=00, second=00
            ),
            "arrival_time": datetime(
                year=2026, month=6, day=15, hour=17, minute=00, second=00
            ),
            "crew": crew_member1.id,
        }

        response = self.client.post(FLIGHT_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_filter_route_by_departure_time(self):
        serializer = FlightListSerializer(self.flight)

        response = self.client.get(FLIGHT_URL, {"departure_time": "2026-06-15"})
        self.assertIn(serializer.data, response.data["results"])

    def test_filter_route_by_arrival_time(self):
        serializer = FlightListSerializer(self.flight)

        response = self.client.get(FLIGHT_URL, {"arrival_time": "2026-06-15"})
        self.assertIn(serializer.data, response.data["results"])


class AdminFlightTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@test.com", password="test123", is_staff=True
        )
        self.client.force_authenticate(self.user)
        self.flight = sample_flight()
        self.route = self.flight.route
        self.airplane = self.flight.airplane

    def test_post_flight(self):
        crew_member1 = CrewMember.objects.create(first_name="John", last_name="Doe")

        payload = {
            "route": self.route.id,
            "airplane": self.airplane.id,
            "departure_time": datetime(
                year=2026, month=6, day=15, hour=15, minute=00, second=00
            ),
            "arrival_time": datetime(
                year=2026, month=6, day=15, hour=17, minute=00, second=00
            ),
            "crew": crew_member1.id,
        }

        response = self.client.post(FLIGHT_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_put_flight(self):

        crew_member1 = CrewMember.objects.create(first_name="Sam", last_name="Doe")
        crew_member2 = CrewMember.objects.create(
            first_name="Arthur", last_name="Stevens"
        )

        flight = self.flight
        airplane = self.flight.airplane
        route = self.flight.route

        payload = {
            "route": route.id,
            "airplane": airplane.id,
            "departure_time": datetime(
                year=2026, month=6, day=15, hour=15, minute=00, second=00
            ),
            "arrival_time": datetime(
                year=2026, month=6, day=15, hour=17, minute=00, second=00
            ),
            "crew": [crew_member1.id, crew_member2.id],
        }

        url = detail_url(flight.id)
        response = self.client.put(url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_flight_session(self):

        url = detail_url(self.flight.id)
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
