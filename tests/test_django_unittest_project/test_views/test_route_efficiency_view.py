from collections.abc import Mapping
from typing import Any
from django import test
from django.db import models
from django_unittest_project.models import Route
from tests.test_django_unittest_project.factories import (
    RouteAssignmentFactory,
    UserFactory,
)
from django import urls as dj_urls
from django.conf import settings
from tests.utils import expected_x_but_got_y, serialize_response


class RouteEfficiencyViewTests(test.TestCase):
    URL = dj_urls.reverse_lazy("route_efficiency")
    LOGIN_URL = dj_urls.reverse_lazy(settings.LOGIN_URL)

    def test_success(self) -> None:
        """
        - Given: `GET` request from an authenticated user specifying an existent `Route`
        - When: request is received
        - Then: a `200` response with the appropriate template rendered in the body and
            the appropriate `context`
        """
        RouteAssignmentFactory.create_batch(3)
        self.client.force_login(UserFactory.create())
        expected_route_data = self.__get_expected_route_data()

        response = self.client.get(self.URL)

        assert response.status_code == 200
        assert (
            response.context["route_data"] == expected_route_data
        ), expected_x_but_got_y(expected_route_data, response.context["route_data"])
        assert "route_efficiency.html" in [
            template.name for template in response.templates
        ]

    def test_unauthenticated(self) -> None:
        """
        - Given: `GET` request from an unauthenticated user
        - When: request is received
        - Then: a `302` response should be sent redirecting the user to the login page
        """
        expected_location_header = f"{self.LOGIN_URL}?next={self.URL}"

        response = self.client.get(self.URL)

        assert response.status_code == 302, serialize_response(response)
        assert (
            response.headers["Location"] == expected_location_header
        ), expected_x_but_got_y(expected_location_header, response.headers["Location"])

    def __get_expected_route_data(self) -> "Mapping[str, Any]":
        return [
            self.__serialize_route(route)
            for route in Route.objects.prefetch_related("routeassignment_set").all()
        ]

    def __serialize_route(self, route: "Route") -> "Mapping[str, Any]":
        assignments = route.routeassignment_set.all()
        total_capacity = assignments.aggregate(models.Sum("vehicle__capacity"))[
            "vehicle__capacity__sum"
        ]
        avg_capacity = assignments.aggregate(models.Avg("vehicle__capacity"))[
            "vehicle__capacity__avg"
        ]
        return {
            "route": route,
            "total_capacity": total_capacity,
            "average_capacity": avg_capacity,
            "assignment_count": assignments.count(),
        }
