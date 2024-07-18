from typing import cast

from django import test, urls as dj_urls
from django.conf import settings
from django.db import models

from django_unittest_project.models import Route
from django_unittest_project.models import RouteAssignment
from tests.test_django_unittest_project.factories import (
    RouteAssignmentFactory,
    RouteFactory,
    UserFactory,
)
from tests.utils import expected_x_but_got_y, serialize_response


class RouteDetailTests(test.TestCase):
    LOGIN_URL = dj_urls.reverse_lazy(settings.LOGIN_URL)

    def setUp(self) -> None:
        self.__route: Route = RouteFactory.create()

    def test_success(self) -> None:
        """
        - Given: `GET` request from an authenticated user specifying an existent `Route`
        - When: request is received
        - Then: a `200` response with the appropriate template rendered in the body and
            the appropriate `context`
        """
        self.client.force_login(UserFactory.create())
        expected_assignment_ids = set(
            cast("RouteAssignment", assignment).pk
            for assignment in RouteAssignmentFactory.create_batch(3, route=self.__route)
        )

        response = self.client.get(self.__get_url_from_route(self.__route))

        actual_assignment_ids = cast(
            "models.QuerySet",
            response.context["assignments"],
        ).values_list("pk", flat=True)

        assert response.status_code == 200
        assert "route_detail.html" in [template.name for template in response.templates]
        assert response.context["route"] == self.__route
        assert set(actual_assignment_ids) == expected_assignment_ids
        assert (
            cast("models.QuerySet", response.context["assignments"]).model
            == RouteAssignment
        )

    def test_unauthenticated(self) -> None:
        """
        - Given: `GET` request from an unauthenticated user
        - When: request is received
        - Then: a `302` response should be sent redirecting the user to the login page
        """
        expected_location_header = (
            f"{self.LOGIN_URL}?next={self.__get_url_from_route(self.__route)}"
        )

        response = self.client.get(self.__get_url_from_route(self.__route))

        assert response.status_code == 302, serialize_response(response)
        assert (
            response.headers["Location"] == expected_location_header
        ), expected_x_but_got_y(expected_location_header, response.headers["Location"])

    def test_non_existent_vehicle(self) -> None:
        """
        - Given: `GET` request from an authenticated user specifying a non existent
            `Route`
        - When: request is received
        - Then: a `404` error response should be sent
        """
        self.client.force_login(UserFactory.create())
        self.__route.delete()

        response = self.client.get(
            self.__get_url_from_route(self.__route),
            content_type="application/json",
        )

        assert response.status_code == 404, serialize_response(response)

    def __get_url_from_route(self, route: "Route") -> str:
        return dj_urls.reverse(
            "route_detail",
            kwargs={"route_number": route.route_number},
        )
