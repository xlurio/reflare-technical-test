import json
from django import test
from django.urls import reverse
import datetime as dt
from decimal import Decimal
from django_unittest_project.models import MaintenanceLog, Vehicle
from tests.test_django_unittest_project.factories import UserFactory, VehicleFactory


class PostTests(test.TestCase):

    def setUp(self) -> None:
        self.__client = test.Client()
        self.__client.force_login(UserFactory.create(is_staff=True))
        self.__vehicle: "Vehicle" = VehicleFactory.create()

    def test_success(self) -> None:
        """
        - Given: `POST` request from a staff user specifying an existent `Vehicle` and
            valid `MaintenanceLog` payload
        - When: request is received
        - Then: a `201` response should be sent with the appropriate message, a
            `MaintenanceLog` should be created from the passed data and the
            `Vehicle.last_maintenance` should be updated
        """
        expected_maintenance_date = dt.date.today()
        expected_description = "test maintenance"
        expected_cost = Decimal("100.00")
        maintenance_logs_count = MaintenanceLog.objects.count()
        response = self.__client.post(
            self.__get_url_from_vehicle(self.__vehicle),
            data={
                "maintenance_date": expected_maintenance_date,
                "description": expected_description,
                "cost": str(expected_cost),
            },
            content_type="application/json"
        )

        maintenance_log = MaintenanceLog.objects.filter(vehicle=self.__vehicle).last()
        self.__vehicle.refresh_from_db()

        assert (
            response.status_code == 201
        ), f"{response.status_code}\n{response.content}"
        assert response.content == json.dumps(
            {"message": "Maintenance log added successfully."}
        ).encode(), response.content
        assert MaintenanceLog.objects.count() > maintenance_logs_count
        assert maintenance_log is not None
        assert maintenance_log.maintenance_date == expected_maintenance_date
        assert maintenance_log.description == expected_description
        assert maintenance_log.cost == expected_cost
        assert self.__vehicle.last_maintenance == maintenance_log.maintenance_date

    def __get_url_from_vehicle(self, vehicle: "Vehicle") -> str:
        return reverse("vehicle_maintenance", kwargs={"vehicle_id": vehicle.vehicle_id})
