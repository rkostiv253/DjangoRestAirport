import pathlib
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify


class Country(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class City(models.Model):
    city = models.CharField(max_length=100)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("city", "country")
        ordering = ["city", "country"]

    def __str__(self):
        return f"{self.city}, {self.country.name}"


class Airport(models.Model):
    name = models.CharField(max_length=100)
    city = models.ForeignKey(City, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class CrewMember(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class AirplaneType(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Airplane(models.Model):
    name = models.CharField(max_length=100, unique=True)
    rows = models.IntegerField()
    seats_in_row = models.IntegerField()
    airplane_type = models.ForeignKey(AirplaneType, on_delete=models.CASCADE)

    @property
    def capacity(self):
        return self.rows * self.seats_in_row

    def __str__(self):
        return self.name


def route_image_path(instance, filename):
    filename = (f"{slugify(instance.id)}-{uuid.uuid4()}"
                + pathlib.Path(filename).suffix)
    return pathlib.Path("uploads/routes/", filename)


class Route(models.Model):
    departure_airport = models.ForeignKey(
        Airport, on_delete=models.CASCADE, related_name="departure_routes"
    )
    destination = models.ForeignKey(
        Airport, on_delete=models.CASCADE, related_name="destination_routes"
    )
    distance = models.IntegerField()
    image = models.ImageField(null=True, upload_to=route_image_path)

    def __str__(self):
        return f"{self.departure_airport} to {self.destination}"


class Flight(models.Model):
    route = models.ForeignKey(
        Route,
        on_delete=models.CASCADE,
        related_name="flights"
    )
    airplane = models.ForeignKey(
        Airplane, on_delete=models.CASCADE, related_name="flights"
    )
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()
    crew = models.ManyToManyField(CrewMember)

    def __str__(self):
        return (
            f"Flight {self.id}. "
            f"{str(self.route)}, "
            f"{self.departure_time}, "
            f"{self.arrival_time}"
        )

    class Meta:
        ordering = ["-departure_time"]


class Order(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    def __str__(self):
        return str(self.created_at)

    class Meta:
        ordering = ["-created_at"]


class Ticket(models.Model):
    row = models.IntegerField()
    seat = models.IntegerField()
    flight = models.ForeignKey(
        Flight,
        on_delete=models.CASCADE,
        related_name="tickets"
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="tickets"
    )

    @staticmethod
    def validate_ticket(row, seat, airplane, error_to_raise):
        for ticket_attr_value, ticket_attr_name, airplane_attr_name in [
            (row, "row", "rows"),
            (seat, "seat", "seats_in_row"),
        ]:
            count_attrs = getattr(airplane, airplane_attr_name)
            if not (1 <= ticket_attr_value <= count_attrs):
                raise error_to_raise(
                    {
                        ticket_attr_name: f"{ticket_attr_name} "
                        f"number must be in available range: "
                        f"(1, {airplane_attr_name}): "
                        f"(1, {count_attrs})"
                    }
                )

    def clean(self):
        Ticket.validate_ticket(
            self.row,
            self.seat,
            self.flight.airplane,
            ValidationError,
        )

    def save(
        self,
        force_insert=False,
        force_update=False,
        using=None,
        update_fields=None,
    ):
        self.full_clean()
        return super(Ticket, self).save(
            force_insert, force_update, using, update_fields
        )

    def __str__(self):
        return f"{str(self.flight)} (row: {self.row}, seat: {self.seat})"

    class Meta:
        unique_together = ("flight", "row", "seat")
        ordering = ["row", "seat"]
