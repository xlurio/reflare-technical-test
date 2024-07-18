from typing import cast
from django import test
from django.db import models
from django_unittest_project.models import MaintenanceLog, Vehicle
from django import urls as dj_urls
from tests.test_django_unittest_project.factories import (
    MaintenanceLogFactory,
    UserFactory,
    VehicleFactory,
)
from tests.utils import expected_x_but_got_y, serialize_response
from django.conf import settings


class GetTests(test.TestCase):
    LOGIN_URL = dj_urls.reverse_lazy(settings.LOGIN_URL)

    def setUp(self) -> None:
        self.__vehicle: "Vehicle" = VehicleFactory.create()

    def test_success(self) -> None:
        """
        - Given: `GET` request from an authenticated user specifying an existent
            `Vehicle`
        - When: request is received
        - Then: a `200` response with the appropriate template rendered in the body and
            the appropriate `context`
        """
        self.client.force_login(UserFactory.create())
        MaintenanceLogFactory.create_batch(3, vehicle=self.__vehicle)
        expected_maintenance_logs = MaintenanceLog.objects.filter(
            vehicle=self.__vehicle
        ).order_by("-maintenance_date")
        expected_maintenance_logs_ids = set(
            expected_maintenance_logs.values_list("pk", flat=True)
        )
        expected_total_cost = expected_maintenance_logs.aggregate(models.Sum("cost"))[
            "cost__sum"
        ]

        response = self.client.get(self.__get_url_from_vehicle(self.__vehicle))

        actual_logs_ids = cast("models.QuerySet", response.context["logs"]).values_list(
            "pk", flat=True
        )

        assert response.status_code == 200
        assert str(response.headers["Content-Type"]).startswith("text/html")
        assert response.context["vehicle"] == self.__vehicle
        assert "vehicle_maintenance.html" in [
            template.name for template in response.templates
        ]
        assert set(actual_logs_ids) == expected_maintenance_logs_ids
        assert response.context["total_cost"] == expected_total_cost

    def test_unauthenticated(self) -> None:
        """
        - Given: `GET` request from an unauthenticated user
        - When: request is received
        - Then: a `302` response should be sent redirecting the user to the login page
        """
        MaintenanceLogFactory.create_batch(3, vehicle=self.__vehicle)
        expected_location_header = (
            f"{self.LOGIN_URL}?next={self.__get_url_from_vehicle(self.__vehicle)}"
        )

        response = self.client.get(self.__get_url_from_vehicle(self.__vehicle))

        assert response.status_code == 302, serialize_response(response)
        assert (
            response.headers["Location"] == expected_location_header
        ), expected_x_but_got_y(expected_location_header, response.headers["Location"])

    def test_non_existent_vehicle(self) -> None:
        """
        - Given: `GET` request from an authenticated user specifying a non existent
            `Vehicle`
        - When: request is received
        - Then: a `404` error response should be sent
        """
        self.client.force_login(UserFactory.create())
        self.__vehicle.delete()

        response = self.client.get(
            self.__get_url_from_vehicle(self.__vehicle),
            content_type="application/json",
        )

        assert response.status_code == 404, serialize_response(response)

    def __get_url_from_vehicle(self, vehicle: "Vehicle") -> str:
        return dj_urls.reverse(
            "vehicle_maintenance", kwargs={"vehicle_id": vehicle.vehicle_id}
        )
