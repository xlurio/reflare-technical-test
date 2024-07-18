from typing import TYPE_CHECKING
from factory.django import DjangoModelFactory
import factory
import random as rd
import datetime as dt
from django.conf import settings

if TYPE_CHECKING:
    from django_unittest_project.users.models import User


def generate_capacity(self: "VehicleFactory") -> int:
    if self.type == "BUS":
        return rd.randint(0, 100)

    elif self.type == "TRAM":
        return rd.randint(0, 250)

    return rd.randint(0, 500)


def generate_last_maintenance() -> dt.date:
    return dt.date.today() - dt.timedelta(rd.randint(0, 30))


def generate_route_assignment_start_time() -> dt.time:
    return dt.time(rd.randint(0, 12), rd.randint(0, 59))


def generate_route_assignment_end_time(self: "RouteAssignmentFactory") -> dt.time:
    start_time: "dt.time" = self.start_time
    return dt.time(rd.randint(start_time.hour + 1, 24), rd.randint(0, 59))


class VehicleFactory(DjangoModelFactory):
    class Meta:
        model = "django_unittest_project.Vehicle"

    vehicle_id = factory.LazyFunction(lambda: rd.randint(0, 999999999))
    type = factory.LazyFunction(lambda: rd.choice(["BUS", "TRAM", "SUBWAY"]))
    capacity = factory.LazyAttribute(generate_capacity)
    last_maintenance = factory.LazyFunction(generate_last_maintenance)


class UserFactory(DjangoModelFactory):
    class Meta:
        model = settings.AUTH_USER_MODEL

    name = "test_user"
    email = "test_user@example.com"

    @factory.post_generation
    def password(obj: "User", create: bool, extracted: str | None, **kwargs) -> None:
        if create:
            UserFactory.set_password(obj, extracted)

    @staticmethod
    def set_password(obj: "User", extracted: str | None) -> None:
        if extracted:
            return obj.set_password(extracted)

        obj.set_password("123")


class MaintenanceLogFactory(DjangoModelFactory):
    class Meta:
        model = "django_unittest_project.MaintenanceLog"

    vehicle = factory.SubFactory(
        "tests.test_django_unittest_project.factories.VehicleFactory"
    )
    maintenance_date = dt.date.today()
    description = factory.Faker("sentence")
    cost = factory.Faker("pydecimal", left_digits=3, right_digits=2, positive=True)


class RouteFactory(DjangoModelFactory):

    class Meta:
        model = "django_unittest_project.Route"

    route_number = factory.LazyFunction(lambda: rd.randint(0, 999999999))
    start_point = factory.Faker("word")
    end_point = factory.Faker("word")


class RouteAssignmentFactory(DjangoModelFactory):

    class Meta:
        model = "django_unittest_project.RouteAssignment"

    vehicle = factory.SubFactory(
        "tests.test_django_unittest_project.factories.VehicleFactory"
    )
    route = factory.SubFactory(
        "tests.test_django_unittest_project.factories.RouteFactory"
    )
    driver_name = factory.Faker("name")
    start_time = factory.LazyFunction(generate_route_assignment_start_time)
    end_time = factory.LazyAttribute(generate_route_assignment_end_time)
