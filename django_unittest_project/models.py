from typing import TYPE_CHECKING
from django.db import models
from django.core.exceptions import ValidationError

if TYPE_CHECKING:
    from django.db.models.manager import RelatedManager


class Vehicle(models.Model):
    TYPES = [
        ("BUS", "Bus"),
        ("TRAM", "Tram"),
        ("SUBWAY", "Subway"),
    ]
    vehicle_id = models.CharField(max_length=10, unique=True)
    type = models.CharField(max_length=6, choices=TYPES)
    capacity = models.PositiveIntegerField()
    last_maintenance = models.DateField()

    def clean(self):
        if self.type == "BUS" and self.capacity > 100:
            raise ValidationError("Buses cannot have a capacity greater than 100.")
        elif self.type == "TRAM" and self.capacity > 250:
            raise ValidationError("Trams cannot have a capacity greater than 250.")

    def __str__(self):
        return f"{self.get_type_display()} - {self.vehicle_id}"


class Route(models.Model):
    routeassignment_set: "RelatedManager[RouteAssignment]"

    route_number = models.CharField(max_length=10, unique=True)
    start_point = models.CharField(max_length=100)
    end_point = models.CharField(max_length=100)
    vehicles = models.ManyToManyField(Vehicle, through="RouteAssignment")

    def __str__(self):
        return f"Route {self.route_number}: {self.start_point} to {self.end_point}"


class RouteAssignment(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    route = models.ForeignKey(Route, on_delete=models.CASCADE)
    driver_name = models.CharField(max_length=100)
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        unique_together = ["vehicle", "start_time", "end_time"]

    def clean(self):
        if self.start_time >= self.end_time:
            raise ValidationError("End time must be after start time.")

    def __str__(self):
        return f"{self.vehicle} on {self.route} ({self.start_time}-{self.end_time})"


class MaintenanceLog(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    maintenance_date = models.DateField()
    description = models.TextField()
    cost = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Maintenance for {self.vehicle} on {self.maintenance_date}"
