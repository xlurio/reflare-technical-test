from typing import TYPE_CHECKING
from factory.django import DjangoModelFactory
import factory
import random as rd
import datetime as dt
from django.conf import settings

if TYPE_CHECKING:
    from django_unittest_project.users.models import User


def generate_vehicle_id() -> str:
    return rd.randint(0, 999999999)


def generate_capacity(self: "VehicleFactory") -> int:
    if self.type == "BUS":
        return rd.randint(0, 100)
    
    elif self.type == "TRAM":
        return rd.randint(0, 250)
    
    return rd.randint(0, 500)


def generate_last_maintenance() -> dt.date:
    return dt.date.today() - dt.timedelta(rd.randint(0, 30))


class VehicleFactory(DjangoModelFactory):
    class Meta:
        model = "django_unittest_project.Vehicle"

    vehicle_id = factory.LazyFunction(generate_vehicle_id)
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
