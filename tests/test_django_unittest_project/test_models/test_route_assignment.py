from django import test
import random as rd
from django_unittest_project.models import RouteAssignment
from tests.test_django_unittest_project.factories import RouteAssignmentFactory
from django.core import exceptions as core_exc
import datetime as dt


class RouteAssignmentTests(test.TestCase):

    def test_valid(self) -> None:
        """
        - Given: `RouteAssignment` with `start_time < end_time`
        - When: `clean` is called
        - Then: `None` should be returned
        """
        start_time = dt.time(rd.randint(0, 22), rd.randint(0, 59))
        end_time = dt.time(rd.randint(start_time.hour, 23), rd.randint(0, 59))
        route_assignment: "RouteAssignment" = RouteAssignmentFactory.create(
            start_time=start_time, end_time=end_time
        )
        assert route_assignment.clean() == None

    def test_invalid(self) -> None:
        """
        - Given: `RouteAssignment` with `start_time >= end_time`
        - When: `clean` is called
        - Then: a `ValidationError` should be raised with the appropriated message
        """
        start_time = dt.time(rd.randint(0, 23), rd.randint(0, 59))
        end_time = dt.time(rd.randint(0, start_time.hour), rd.randint(0, 59))
        route_assignment: "RouteAssignment" = RouteAssignmentFactory.create(
            start_time=start_time, end_time=end_time
        )

        with self.assertRaises(core_exc.ValidationError) as context:
            route_assignment.clean()
            assert context.exception.message == "End time must be after start time."
