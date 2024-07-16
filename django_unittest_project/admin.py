from django.contrib import admin
from .models import Vehicle, Route, RouteAssignment, MaintenanceLog

admin.site.register(Vehicle)
admin.site.register(Route)
admin.site.register(RouteAssignment)
admin.site.register(MaintenanceLog)
