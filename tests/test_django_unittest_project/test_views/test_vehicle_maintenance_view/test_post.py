import dataclasses as dc
import datetime as dt
import json
import random as rd
from collections.abc import Mapping
from decimal import Decimal
from typing import Any
from unittest import mock as ut_mock

from django import http as dj_http
from django import test
from django import urls as dj_urls
from django.conf import settings
from django.core import exceptions as core_exc
from django.test import client as test_client

from django_unittest_project.models import MaintenanceLog
from django_unittest_project.models import Vehicle
from tests.test_django_unittest_project.factories import UserFactory
from tests.test_django_unittest_project.factories import VehicleFactory
from tests.utils import expected_x_but_got_y
from tests.utils import serialize_response


class PostTestsConstants:

    LOGIN_URL = dj_urls.reverse_lazy(settings.LOGIN_URL)


def _make_fake_payload(
    *,
    maintenance_date: dt.date | None = None,
    description: str | None = None,
    cost: Decimal | None = None,
):
    maintenance_date = dt.date.today() if maintenance_date is None else maintenance_date
    return {
        "maintenance_date": maintenance_date,
        "description": "test maintenance" if description is None else description,
        "cost": "100.00" if cost is None else cost,
    }


@dc.dataclass
class SuccessArrangement:
    expected_maintenance_date: dt.date
    expected_description: str
    expected_cost: Decimal
    maintenance_logs_count: int

    @property
    def expected_cost_as_str(self) -> str:
        return str(self.expected_cost)


@dc.dataclass
class UnauthenticatedArrangement:
    maintenance_date: dt.date
    maintenance_logs_count: int
    prev_last_maintenance: dt.date
    endpoint_url: str

    @property
    def expected_location_header(self) -> str:
        return f"{PostTestsConstants.LOGIN_URL}?next={self.endpoint_url}"


@dc.dataclass
class MissingFieldsArrangement:
    maintenance_logs_count: int
    prev_last_maintenance: dt.date

    def __post_init__(self):
        self.__request_payload = _make_fake_payload()
        fields = list(self.__request_payload.keys())
        self.__field_to_remove = rd.choice(fields)
        self.__request_payload.pop(self.__field_to_remove)

    @property
    def expected_content(self) -> str:
        message = f"Missing required field: '{self.__field_to_remove}'"
        return json.dumps({"error": message}).encode()

    @property
    def request_payload(self) -> "Mapping[str, Any]":
        return self.__request_payload


@dc.dataclass
class ValidationErrorArrangement:
    maintenance_logs_count: int
    prev_last_maintenance: dt.date
    exception: str

    @property
    def expected_content(self) -> str:
        message = str(self.exception)
        return json.dumps({"error": message}).encode()


class PostTests(test.TestCase):
    def setUp(self) -> None:
        self.__vehicle: Vehicle = VehicleFactory.create()

    def test_success(self) -> None:
        """
        - Given: `POST` request from a staff user specifying an existent `Vehicle` and
            valid `MaintenanceLog` payload
        - When: request is received
        - Then: a `201` response should be sent with the appropriate message, a
            `MaintenanceLog` should be created from the passed data and the
            `Vehicle.last_maintenance` should be updated
        """
        arrangement = SuccessArrangement(
            expected_maintenance_date=dt.date.today(),
            expected_description="test maintenance",
            expected_cost=Decimal("100.00"),
            maintenance_logs_count=MaintenanceLog.objects.count(),
        )
        self.client.force_login(UserFactory.create(is_staff=True))

        response = self.client.post(
            self.__get_url_from_vehicle(self.__vehicle),
            data=_make_fake_payload(),
            content_type="application/json",
        )

        self.__vehicle.refresh_from_db()

        self.__assert_success(arrangement, response)

    def __assert_success(
        self, arrangement: "SuccessArrangement", response: dj_http.HttpResponse,
    ) -> None:
        maintenance_log = MaintenanceLog.objects.filter(vehicle=self.__vehicle).last()

        assert response.status_code == 201, serialize_response(response)
        assert (
            response.content
            == json.dumps({"message": "Maintenance log added successfully."}).encode()
        ), serialize_response(response)
        assert MaintenanceLog.objects.count() > arrangement.maintenance_logs_count
        assert maintenance_log is not None
        assert maintenance_log.maintenance_date == arrangement.expected_maintenance_date
        assert maintenance_log.description == arrangement.expected_description
        assert maintenance_log.cost == arrangement.expected_cost
        assert self.__vehicle.last_maintenance == maintenance_log.maintenance_date

    def test_unauthenticated(self) -> None:
        """
        - Given: `POST` request from unauthenticated user
        - When: request is received
        - Then: a `302` response should be sent redirecting the user to the login page,
            no `MaintenanceLog` should be created neither the `last_maintenance` of the
            vehicle should change
        """
        arrangement = UnauthenticatedArrangement(
            maintenance_date=dt.date.today(),
            maintenance_logs_count=MaintenanceLog.objects.count(),
            prev_last_maintenance=self.__vehicle.last_maintenance,
            endpoint_url=self.__get_url_from_vehicle(self.__vehicle),
        )

        response = self.client.post(
            self.__get_url_from_vehicle(self.__vehicle),
            data={
                "maintenance_date": arrangement.maintenance_date,
                "description": "test maintenance",
                "cost": "100.00",
            },
            content_type="application/json",
        )

        self.__vehicle.refresh_from_db()
        assert response.status_code == 302, serialize_response(response)
        assert (
            response.headers["Location"] == arrangement.expected_location_header
        ), expected_x_but_got_y(
            arrangement.expected_location_header, response.headers["Location"],
        )
        assert arrangement.maintenance_logs_count == MaintenanceLog.objects.count()
        assert self.__vehicle.last_maintenance == arrangement.prev_last_maintenance

    def test_non_staff(self) -> None:
        """
        - Given: `POST` request from a non staff user
        - When: request is received
        - Then: a `403` error response should be sent with the appropriate error
            message, no `MaintenanceLog` should be created neither the
            `last_maintenance` of the `Vehicle` should change
        """
        maintenance_date = dt.date.today()
        maintenance_logs_count = MaintenanceLog.objects.count()
        prev_last_maintenance = self.__vehicle.last_maintenance
        expected_content = json.dumps(
            {"error": "You do not have permission to perform this action."},
        ).encode()

        self.client.force_login(UserFactory.create(is_staff=False))

        response = self.client.post(
            self.__get_url_from_vehicle(self.__vehicle),
            data={
                "maintenance_date": maintenance_date,
                "description": "test maintenance",
                "cost": "100.00",
            },
            content_type="application/json",
        )

        self.__vehicle.refresh_from_db()

        assert response.status_code == 403, serialize_response(response)
        assert response.content == expected_content, serialize_response(response)
        assert maintenance_logs_count == MaintenanceLog.objects.count()
        assert self.__vehicle.last_maintenance == prev_last_maintenance

    def test_non_existent_vehicle(self) -> None:
        """
        - Given: `POST` request from a staff user specifying a non existent `Vehicle`
        - When: request is received
        - Then: a `404` error response should be sent, and no `MaintenanceLog` should be
            created
        """
        maintenance_date = dt.date.today()
        maintenance_logs_count = MaintenanceLog.objects.count()

        self.client.force_login(UserFactory.create(is_staff=True))
        self.__vehicle.delete()

        response = self.client.post(
            self.__get_url_from_vehicle(self.__vehicle),
            data={
                "maintenance_date": maintenance_date,
                "description": "test maintenance",
                "cost": "100.00",
            },
            content_type="application/json",
        )

        assert response.status_code == 404, serialize_response(response)
        assert maintenance_logs_count == MaintenanceLog.objects.count()

    def test_invalid_json(self) -> None:
        """
        - Given: `POST` request from a staff user with an invalid JSON on the body
        - When: request is received
        - Then: a `400` error response should be send with the appropriate message, no
            `MaintenanceLog` should be created neither the `last_maintenance` of the
            `Vehicle` should change
        """
        maintenance_date = dt.date.today()
        maintenance_logs_count = MaintenanceLog.objects.count()
        prev_last_maintenance = self.__vehicle.last_maintenance
        expected_content = json.dumps({"error": "Invalid JSON"}).encode()

        self.client.force_login(UserFactory.create(is_staff=True))

        response = self.client.post(
            self.__get_url_from_vehicle(self.__vehicle),
            data={
                "maintenance_date": maintenance_date,
                "description": "test maintenance",
                "cost": "100.00",
            },
            content_type=test_client.MULTIPART_CONTENT,
        )

        self.__vehicle.refresh_from_db()

        assert response.status_code == 400, serialize_response(response)
        assert response.content == expected_content, serialize_response(response)
        assert maintenance_logs_count == MaintenanceLog.objects.count()
        assert self.__vehicle.last_maintenance == prev_last_maintenance

    def test_missing_fields(self) -> None:
        """
        - Given: `POST` request from a staff user but the body misses any field
        - When: request is received
        - Then: a `400` error response should be send with the appropriate message, no
            `MaintenanceLog` should be created neither the `last_maintenance` of the
            `Vehicle` should change
        """
        arrangement = MissingFieldsArrangement(
            maintenance_logs_count=MaintenanceLog.objects.count(),
            prev_last_maintenance=self.__vehicle.last_maintenance,
        )

        self.client.force_login(UserFactory.create(is_staff=True))

        response = self.client.post(
            self.__get_url_from_vehicle(self.__vehicle),
            data=arrangement.request_payload,
            content_type="application/json",
        )

        self.__vehicle.refresh_from_db()

        assert response.status_code == 400, serialize_response(response)
        assert response.content == arrangement.expected_content, expected_x_but_got_y(
            response.content, arrangement.expected_content,
        )
        assert arrangement.maintenance_logs_count == MaintenanceLog.objects.count()
        assert self.__vehicle.last_maintenance == arrangement.prev_last_maintenance

    @ut_mock.patch.object(MaintenanceLog, "full_clean")
    def test_validation_error(self, mock_full_clean: "ut_mock.MagicMock") -> None:
        """
        - Given: `POST` request from a staff user but the validation of the
            `MaintenanceLog` fails
        - When: request is received
        - Then: a `400` error response should be send with the appropriate message, no
            `MaintenanceLog` should be created neither the `last_maintenance` of the
            `Vehicle` should change
        """
        arrangement = ValidationErrorArrangement(
            maintenance_logs_count=MaintenanceLog.objects.count(),
            prev_last_maintenance=self.__vehicle.last_maintenance,
            exception=core_exc.ValidationError("test"),
        )
        mock_full_clean.side_effect = arrangement.exception

        self.client.force_login(UserFactory.create(is_staff=True))

        response = self.client.post(
            self.__get_url_from_vehicle(self.__vehicle),
            data=_make_fake_payload(),
            content_type="application/json",
        )

        self.__vehicle.refresh_from_db()

        assert response.status_code == 400, serialize_response(response)
        assert response.content == arrangement.expected_content, expected_x_but_got_y(
            response.content, arrangement.expected_content,
        )
        assert arrangement.maintenance_logs_count == MaintenanceLog.objects.count()
        assert self.__vehicle.last_maintenance == arrangement.prev_last_maintenance

    def __get_url_from_vehicle(self, vehicle: "Vehicle") -> str:
        return dj_urls.reverse(
            "vehicle_maintenance", kwargs={"vehicle_id": vehicle.vehicle_id},
        )
