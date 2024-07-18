from django.shortcuts import render, get_object_or_404
from django.views import View
from django.db.models import Sum, Avg
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from .models import Vehicle, Route, MaintenanceLog
import json
from django.core.exceptions import ValidationError


class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff


class VehicleListView(LoginRequiredMixin, View):
    def get(self, request):
        vehicles = Vehicle.objects.all()
        return render(request, 'vehicle_list.html', {'vehicles': vehicles})


class RouteDetailView(LoginRequiredMixin, View):
    def get(self, request, route_number):
        route = get_object_or_404(Route, route_number=route_number)
        assignments = route.routeassignment_set.all().order_by('start_time')
        return render(request, 'route_detail.html', {'route': route, 'assignments': assignments})


class VehicleMaintenanceView(LoginRequiredMixin, View):
    def get(self, request, vehicle_id):
        vehicle = get_object_or_404(Vehicle, vehicle_id=vehicle_id)
        maintenance_logs = MaintenanceLog.objects.filter(vehicle=vehicle).order_by('-maintenance_date')
        total_cost = maintenance_logs.aggregate(Sum('cost'))['cost__sum']
        return render(request, 'vehicle_maintenance.html',
                      {'vehicle': vehicle, 'logs': maintenance_logs, 'total_cost': total_cost})

    @method_decorator(csrf_exempt)
    @method_decorator(require_http_methods(["POST"]))
    def post(self, request, vehicle_id):
        if not request.user.is_staff:
            return JsonResponse({'error': 'You do not have permission to perform this action.'}, status=403)

        vehicle = get_object_or_404(Vehicle, vehicle_id=vehicle_id)

        try:
            data = json.loads(request.body)
            maintenance_log = MaintenanceLog(
                vehicle=vehicle,
                maintenance_date=data['maintenance_date'],
                description=data['description'],
                cost=data['cost']
            )
            maintenance_log.full_clean()
            maintenance_log.save()

            # Update the vehicle's last_maintenance date
            vehicle.last_maintenance = maintenance_log.maintenance_date
            vehicle.save()

            return JsonResponse({'message': 'Maintenance log added successfully.'}, status=201)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except KeyError as e:
            return JsonResponse({'error': f'Missing required field: {str(e)}'}, status=400)
        except ValidationError as e:
            return JsonResponse({'error': str(e)}, status=400)


class RouteEfficiencyView(LoginRequiredMixin, View):
    def get(self, request):
        routes = Route.objects.all()
        route_data = []
        for route in routes:
            assignments = route.routeassignment_set.all()
            total_capacity = assignments.aggregate(Sum('vehicle__capacity'))['vehicle__capacity__sum']
            avg_capacity = assignments.aggregate(Avg('vehicle__capacity'))['vehicle__capacity__avg']
            route_data.append({
                'route': route,
                'total_capacity': total_capacity,
                'average_capacity': avg_capacity,
                'assignment_count': assignments.count()
            })
        return render(request, 'route_efficiency.html', {'route_data': route_data})
