from typing import cast

from django import test, urls as dj_urls
from django.db import models

from django_unittest_project.models import Vehicle
from tests.test_django_unittest_project.factories import UserFactory, VehicleFactory
from tests.utils import expected_x_but_got_y, serialize_response
from django.conf import settings


class VehicleListViewTests(test.TestCase):
    URL = dj_urls.reverse_lazy("vehicle_list")
    LOGIN_URL = dj_urls.reverse_lazy(settings.LOGIN_URL)

    def test_success(self) -> None:
        """
        - Given: `GET` request from an authenticated user
        - When: request is received
        - Then: a `200` response with the appropriate template rendered in the body and
            the appropriate `context`
        """
        expected_vehicles_ids = set(
            cast("Vehicle", vehicle).pk for vehicle in VehicleFactory.create_batch(3)
        )
        self.client.force_login(UserFactory.create())

        response = self.client.get(self.URL)

        actual_vehicles_ids = cast(
            "models.QuerySet", response.context["vehicles"]
        ).values_list("pk", flat=True)

        assert response.status_code == 200
        assert "vehicle_list.html" in [template.name for template in response.templates]
        assert cast("models.QuerySet", response.context["vehicles"]).model == Vehicle
        assert set(actual_vehicles_ids) == expected_vehicles_ids

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
