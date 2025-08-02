import os
import tempfile

from PIL import Image
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status
from airport.models import Route
from airport.serializers import RouteListSerializer, RouteDetailSerializer

from airport.tests.test_flight_api import (
    sample_route,
    sample_flight,
    FLIGHT_URL,
    ROUTE_URL,
    sample_departure_airport,
    sample_destination,
)


def detail_url(route_id):
    return reverse("airport:route-detail", args=[route_id])


def image_upload_url(route_id):
    return reverse("airport:route-upload-image", args=[route_id])


class UnauthenticatedRouteApiTests(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        response = self.client.get(ROUTE_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedRouteApiTest(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@test.com",
            password="test123",
        )

        self.client.force_authenticate(user=self.user)
        self.route = sample_route()
        self.departure_airport = self.route.departure_airport
        self.destination = self.route.destination

    def test_get_routes(self):
        routes = self.client.get(ROUTE_URL)
        self.assertEqual(routes.status_code, status.HTTP_200_OK)

    def test_retrieve_route(self):

        url = detail_url(self.route.id)
        response = self.client.get(url)

        serializer = RouteDetailSerializer(self.route)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_create_route_forbidden(self):
        payload = {
            "departure_airport": self.departure_airport.id,
            "destination": self.destination.id,
            "distance": 1200,
        }

        response = self.client.post(ROUTE_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_filter_route_by_departure_city(self):
        serializer = RouteListSerializer(self.route)

        response = self.client.get(ROUTE_URL, {"departure_city": "New York"})
        self.assertIn(serializer.data, response.data["results"])

    def test_filter_route_by_destination_city(self):
        serializer = RouteListSerializer(self.route)

        response = self.client.get(ROUTE_URL, {"destination_city": "London"})
        self.assertIn(serializer.data, response.data["results"])


class AdminRouteTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@test.com", password="test123", is_staff=True
        )
        self.client.force_authenticate(self.user)
        self.route = sample_route()
        self.departure_airport = self.route.departure_airport
        self.destination = self.route.destination

    def test_create_route(self):
        payload = {
            "departure_airport": self.departure_airport.id,
            "destination": self.destination.id,
            "distance": 1200,
        }
        response = self.client.post(ROUTE_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class RouteImageUploadTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_superuser(
            "admin@myproject.com", "password"
        )
        self.client.force_authenticate(self.user)
        self.route = sample_route()
        self.flight = sample_flight(route=self.route)

    def tearDown(self):
        self.route.image.delete()

    def test_upload_image_to_route(self):
        url = image_upload_url(self.route.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            res = self.client.post(url, {"image": ntf}, format="multipart")
        self.route.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("image", res.data)
        self.assertTrue(os.path.exists(self.route.image.path))

    def test_upload_image_bad_request(self):
        """Test uploading an invalid image"""
        url = image_upload_url(self.route.id)
        res = self.client.post(url, {"image": "not image"}, format="multipart")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_image_to_route_list(self):
        url = ROUTE_URL
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            res = self.client.post(
                url,
                {
                    "distance": 5567,
                    "departure_airport": sample_departure_airport().id,
                    "destination": sample_destination().id,
                    "image": ntf,
                },
                format="multipart",
            )

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        route = Route.objects.get(pk=self.route.id)
        self.assertFalse(route.image)

    def test_image_url_is_shown_on_route_detail(self):
        url = image_upload_url(self.route.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            self.client.post(url, {"image": ntf}, format="multipart")
        res = self.client.get(detail_url(self.route.id))

        self.assertIn("image", res.data)

    def test_image_url_is_shown_on_route_list(self):
        url = image_upload_url(self.route.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            self.client.post(url, {"image": ntf}, format="multipart")
        res = self.client.get(ROUTE_URL)

        self.assertIn("image", res.data["results"][0].keys())

    def test_image_url_is_shown_on_route_detail(self):
        url = image_upload_url(self.route.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            self.client.post(url, {"image": ntf}, format="multipart")
        res = self.client.get(FLIGHT_URL)

        self.assertIn("route_image", res.data["results"][0].keys())
