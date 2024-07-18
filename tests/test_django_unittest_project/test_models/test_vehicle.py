from django import test

from django_unittest_project.models import Vehicle
from tests.test_django_unittest_project.factories import VehicleFactory
import random as rd
from django.core import exceptions as core_exc


class VehicleTests(test.TestCase):

    def test_bus(self) -> None:
        """
        - Given: `Vehicle` with `type == "BUS"` and `capacity <= 100`
        - When: `clean` is called
        - Then: `None` should be returned
        """
        vehicle: "Vehicle" = VehicleFactory.create(
            type="BUS", capacity=rd.randint(1, 100)
        )
        assert vehicle.clean() == None

    def test_tram(self) -> None:
        """
        - Given: `Vehicle` with `type == "TRAM"` and `capacity <= 250`
        - When: `clean` is called
        - Then: `None` should be returned
        """
        vehicle: "Vehicle" = VehicleFactory.create(
            type="TRAM", capacity=rd.randint(1, 250)
        )
        assert vehicle.clean() == None

    def test_subway(self) -> None:
        """
        - Given: `Vehicle` with `type == "SUBWAY"`
        - When: `clean` is called
        - Then: `None` should be returned
        """
        vehicle: "Vehicle" = VehicleFactory.create(type="SUBWAY")
        assert vehicle.clean() == None

    def test_bus_invalid(self) -> None:
        """
        - Given: `Vehicle` with `type == "BUS"` and `capacity > 100`
        - When: `clean` is called
        - Then: a `ValidationError` should be raised with the appropriated message
        """
        vehicle: "Vehicle" = VehicleFactory.create(
            type="BUS", capacity=rd.randint(101, 500)
        )

        with self.assertRaises(core_exc.ValidationError) as context:
            vehicle.clean()
            assert context.exception.message == "Buses cannot have a capacity greater than 100."

    def test_tram_invalid(self) -> None:
        """
        - Given: `Vehicle` with `type == "TRAM"` and `capacity > 250`
        - When: `clean` is called
        - Then: a `ValidationError` should be raised with the appropriated message
        """
        vehicle: "Vehicle" = VehicleFactory.create(
            type="TRAM", capacity=rd.randint(251, 500)
        )

        with self.assertRaises(core_exc.ValidationError) as context:
            vehicle.clean()
            assert context.exception.message == "Trams cannot have a capacity greater than 250."
