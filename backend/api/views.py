from datetime import timedelta, datetime, date
from collections import OrderedDict
from decimal import Decimal, InvalidOperation

from django.http import FileResponse, JsonResponse
from django.views.decorators.http import require_GET
from django.shortcuts import get_object_or_404
from django.db.models import F, Avg, Count, Q, DurationField, ExpressionWrapper, Sum, Value, DecimalField
from django.db.models.functions import TruncDay, TruncWeek, Coalesce
from django.utils import timezone

from django.conf import settings
from rest_framework.views import APIView
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateAPIView
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import PermissionDenied
from django_filters import rest_framework as filters
from django_filters.rest_framework import DjangoFilterBackend

from .models import Department, Report, Supplier, User, Product, StockMovement, Ticket, Order, OrderItem, Customer, Invoice, LeaveRequest, Attendance, Contract, PayrollEntry, SystemStatus
from .serializers import (
    CustomerSalesSummarySerializer,
    DepartmentSerializer,
    EmployeeCreateSerializer,
    EmployeeListSerializer,
    InvoiceListSerializer,
    OrderCreateSerializer,
    OrderDetailSerializer,
    OrderListSerializer,
    ProductSerializer,
    ReportSerializer,
    SupplierSerializer,
    StockMovementSerializer,
    SystemStatusSerializer,
    TicketCreateSerializer,
    TicketSerializer,
    TicketUpdateSerializer,
)


# Create your views here.
@require_GET
def is_even(request):
    try:
        number = int(request.GET.get("number"))
        result = number % 2 == 0
        return JsonResponse({"even": result})
    except (TypeError, ValueError):
        return JsonResponse(
            {"error": "Invalid or missing number parameter"}, status=400
        )


class LoginView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            acces_token = response.data.get("access")
            refresh_token = response.data.get("refresh")

            response.set_cookie(
                key=settings.SIMPLE_JWT["AUTH_COOKIE"],
                value=acces_token,
                httponly=True,
                secure=False,  # Set to True in production with HTTPS
                samesite="Lax",
                path="/",
            )
            response.set_cookie(
                key=settings.SIMPLE_JWT["AUTH_COOKIE_REFRESH"],
                value=refresh_token,
                httponly=True,
                secure=False,  # Set to True in production with HTTPS
                samesite="Lax",
                path="/api/auth/refresh/",
            )
        return response


class RefreshTokenView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        refresh = request.COOKIES.get(settings.SIMPLE_JWT["AUTH_COOKIE_REFRESH"])
        if refresh:
            request.data["refresh"] = refresh

        response = super().post(request, *args, **kwargs)

        if response.status_code == 200:
            access_token = response.data.get("access")
            response.set_cookie(
                key=settings.SIMPLE_JWT["AUTH_COOKIE"],
                value=access_token,
                httponly=True,
                secure=False,
                samesite="Lax",
                path="/",
            )
            response.data = {"detail": "Refresh success"}
        return response


from rest_framework_simplejwt.tokens import RefreshToken

from rest_framework.permissions import IsAuthenticated


class LogoutView(APIView):
    def post(self, request):
        try:
            refresh_token = request.COOKIES.get(settings.SIMPLE_JWT["AUTH_COOKIE_REFRESH"])
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception:
            pass
        
        response = Response({"detail": "Logout successful"}, status=status.HTTP_200_OK)
        response.delete_cookie(settings.SIMPLE_JWT["AUTH_COOKIE"])
        response.delete_cookie(settings.SIMPLE_JWT["AUTH_COOKIE_REFRESH"])
        return response


class UserMeView(APIView):
    # For development/testing we allow public access so the frontend can show the low-stock demo
    # In production revert this to IsAuthenticated or add proper auth checks.
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return JsonResponse(
            {
                "username": request.user.username,
                "email": request.user.email,
                "role": request.user.role,
                "message": "Daca apare asta, inseamna ca sunt smecher rau de tot sa mor eu",
            }
        )


class DepartmentListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role not in [User.Role.CEO, User.Role.HR]:
            return Response({"detail": "Only CEO and HR can view departments."}, status=status.HTTP_403_FORBIDDEN)

        departments = Department.objects.all()
        serializer = DepartmentSerializer(departments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        if request.user.role != User.Role.CEO:
            return Response({"detail": "Only CEOs can create departments."}, status=status.HTTP_403_FORBIDDEN)

        serializer = DepartmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class DepartmentDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, id):
        if request.user.role != User.Role.CEO:
            return Response({"detail": "Only CEOs can remove departments."}, status=status.HTTP_403_FORBIDDEN)

        department = get_object_or_404(Department, id=id)
        department.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class EmployeePagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class EmployeeListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role not in [User.Role.CEO, User.Role.HR]:
            return Response({"detail": "Only CEO and HR can view employees."}, status=status.HTTP_403_FORBIDDEN)

        queryset = User.objects.select_related('department').all().order_by('id')

        search = request.query_params.get('search', '').strip()
        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
                | Q(username__icontains=search)
            )

        department_filter = request.query_params.get('department')
        if department_filter:
            if department_filter.isdigit():
                queryset = queryset.filter(department_id=int(department_filter))
            else:
                queryset = queryset.filter(department__slug=department_filter)

        is_active_filter = request.query_params.get('is_active')
        if is_active_filter is not None:
            normalized = is_active_filter.strip().lower()
            if normalized in ['true', '1', 'yes']:
                queryset = queryset.filter(is_active=True)
            elif normalized in ['false', '0', 'no']:
                queryset = queryset.filter(is_active=False)

        paginator = EmployeePagination()
        paginated = paginator.paginate_queryset(queryset, request)
        serializer = EmployeeListSerializer(paginated, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        if request.user.role not in [User.Role.CEO, User.Role.HR]:
            return Response({"detail": "Only CEO and HR can create employees."}, status=status.HTTP_403_FORBIDDEN)

        serializer = EmployeeCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        employee = serializer.save()
        response_serializer = EmployeeListSerializer(employee)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class EmployeeDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        if request.user.role not in [User.Role.CEO, User.Role.HR]:
            return Response({"detail": "Only CEO and HR can view employee details."}, status=status.HTTP_403_FORBIDDEN)

        employee = get_object_or_404(User.objects.select_related('department'), id=id)
        serializer = EmployeeListSerializer(employee)
        return Response(serializer.data, status=status.HTTP_200_OK)


class EmployeeStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role not in [User.Role.CEO, User.Role.HR]:
            return Response({"detail": "Only CEO and HR can view employee stats."}, status=status.HTTP_403_FORBIDDEN)

        base = User.objects.select_related('department').all()

        stats = base.aggregate(
            total=Count('id'),
            active=Count('id', filter=Q(is_active=True)),
            full_time=Count('id', filter=Q(full_time=True)),
        )

        department_rows = (
            base.values('department__name')
            .annotate(count=Count('id'))
            .order_by('department__name')
        )

        departments = []
        for row in department_rows:
            departments.append({
                'name': row['department__name'] or 'Unassigned',
                'count': row['count'],
            })

        return Response(
            {
                'total': stats['total'],
                'active': stats['active'],
                'full_time': stats['full_time'],
                'departments': departments,
            },
            status=status.HTTP_200_OK,
        )


class HrDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role not in [User.Role.CEO, User.Role.HR]:
            return Response({"detail": "Only CEO and HR can view HR dashboard KPIs."}, status=status.HTTP_403_FORBIDDEN)

        today = timezone.localdate()
        month_start = today.replace(day=1)

        employees = User.objects.all()
        total_employees = employees.count()
        active_employees = employees.filter(is_active=True).count()
        full_time_employees = employees.filter(full_time=True).count()

        new_hires_this_month = employees.filter(start_date__gte=month_start, start_date__lte=today).count()

        leave_requests_this_month = LeaveRequest.objects.filter(
            created_at__date__gte=month_start,
            created_at__date__lte=today,
        ).count()
        pending_leave_requests = LeaveRequest.objects.filter(status=LeaveRequest.Status.PENDING).count()

        non_full_time = max(total_employees - full_time_employees, 0)
        retention_rate = round((active_employees / total_employees) * 100, 1) if total_employees else 0.0

        return Response(
            {
                'total_employees': total_employees,
                'new_hires_this_month': new_hires_this_month,
                'leave_requests_this_month': leave_requests_this_month,
                'pending_leave_requests': pending_leave_requests,
                'full_time_employees': full_time_employees,
                'non_full_time_employees': non_full_time,
                'retention_rate': retention_rate,
                'active_employees': active_employees,
            },
            status=status.HTTP_200_OK,
        )


class CeoHrSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    @staticmethod
    def _department_matches_role(department, role_keyword):
        slug = (getattr(department, 'slug', '') or '').strip().lower()
        name = (getattr(department, 'name', '') or '').strip().lower()
        keyword = role_keyword.lower().strip()
        return keyword in slug or keyword in name

    def get(self, request):
        if request.user.role != User.Role.CEO:
            return Response({"detail": "Only CEO can view HR summary."}, status=status.HTTP_403_FORBIDDEN)

        today = timezone.localdate()

        current_leaves = LeaveRequest.objects.filter(
            status=LeaveRequest.Status.APPROVED,
            from_date__lte=today,
            to_date__gte=today,
        )

        leave_by_department = {
            row['department_id']: row['count']
            for row in (
                current_leaves.values('department_id').annotate(count=Count('id'))
            )
        }

        department_headcount = []
        departments = Department.objects.order_by('name')
        for department in departments:
            mapped_role = None
            if self._department_matches_role(department, 'it'):
                mapped_role = User.Role.IT
            elif self._department_matches_role(department, 'sales'):
                mapped_role = User.Role.SALES
            elif self._department_matches_role(department, 'hr'):
                mapped_role = User.Role.HR
            elif self._department_matches_role(department, 'inventory'):
                mapped_role = User.Role.INVENTORY

            users_qs = User.objects.filter(department=department)
            leaves_qs = current_leaves.filter(department=department)

            if mapped_role is not None:
                users_qs = User.objects.filter(
                    Q(department=department) | (Q(department__isnull=True) & Q(role=mapped_role))
                )
                leaves_qs = current_leaves.filter(
                    Q(department=department) | (Q(department__isnull=True) & Q(employee__role=mapped_role))
                )

            total = users_qs.count()
            on_leave = leaves_qs.count()
            active = users_qs.filter(is_active=True).count()
            active_now = max(active - on_leave, 0)
            utilisation_pct = round((active_now / total) * 100, 1) if total else 0.0

            department_headcount.append(
                {
                    'department': department.name,
                    'total': total,
                    'active': active_now,
                    'on_leave': on_leave,
                    'utilisation_pct': utilisation_pct,
                }
            )

        six_weeks_ago = today - timedelta(weeks=5)
        week_start = six_weeks_ago - timedelta(days=six_weeks_ago.weekday())

        attendance_rows = (
            Attendance.objects.filter(date__gte=week_start, date__lte=today)
            .annotate(week=TruncWeek('date'))
            .values('week')
            .annotate(
                total=Count('id'),
                attended=Count('id', filter=Q(status__in=[Attendance.Status.PRESENT, Attendance.Status.REMOTE])),
            )
            .order_by('week')
        )

        attendance_by_week = {}
        for row in attendance_rows:
            week_value = row['week']
            week_date = week_value.date() if hasattr(week_value, 'date') else week_value
            key = week_date.isoformat()

            total_count = row['total'] or 0
            attended_count = row['attended'] or 0
            rate = round((attended_count / total_count) * 100, 1) if total_count else 0.0

            attendance_by_week[key] = rate

        attendance_rate_weeks = []
        for index in range(6):
            current_week = week_start + timedelta(weeks=index)
            week_key = current_week.isoformat()
            attendance_rate_weeks.append(
                {
                    'week_start': week_key,
                    'attendance_rate': attendance_by_week.get(week_key, 0.0),
                }
            )

        return Response(
            {
                'department_headcount': department_headcount,
                'attendance_rate_weeks': attendance_rate_weeks,
            },
            status=status.HTTP_200_OK,
        )


class HrAttendanceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role not in [User.Role.CEO, User.Role.HR]:
            return Response({"detail": "Only CEO and HR can view attendance."}, status=status.HTTP_403_FORBIDDEN)

        week_raw = request.query_params.get('week')
        today = timezone.localdate()

        if week_raw:
            parsed_week_start = None
            try:
                parsed_week_start = datetime.strptime(week_raw, '%Y-%m-%d').date()
            except ValueError:
                try:
                    parsed_week_start = datetime.strptime(f'{week_raw}-1', '%G-W%V-%u').date()
                except ValueError:
                    return Response({'detail': 'Invalid week format. Use YYYY-MM-DD or YYYY-Www.'}, status=status.HTTP_400_BAD_REQUEST)

            week_start = parsed_week_start - timedelta(days=parsed_week_start.weekday())
        else:
            week_start = today - timedelta(days=today.weekday())

        days = [week_start + timedelta(days=offset) for offset in range(7)]
        week_end = days[-1]

        attendance_rows = Attendance.objects.filter(date__gte=week_start, date__lte=week_end).select_related('employee')
        by_key = {(row.employee_id, row.date.isoformat()): row.status for row in attendance_rows}

        employees = User.objects.select_related('department').all().order_by('id')
        employee_grid = []
        for employee in employees:
            statuses = {}
            for day in days:
                day_key = day.isoformat()
                statuses[day_key] = by_key.get((employee.id, day_key), None)

            full_name = f'{employee.first_name} {employee.last_name}'.strip() or employee.username
            employee_grid.append(
                {
                    'employee_id': employee.id,
                    'employee_name': full_name,
                    'department': employee.department.name if employee.department else None,
                    'statuses': statuses,
                }
            )

        return Response(
            {
                'week_start': week_start.isoformat(),
                'week_end': week_end.isoformat(),
                'days': [d.isoformat() for d in days],
                'grid': employee_grid,
            },
            status=status.HTTP_200_OK,
        )


class LeaveRequestListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.role not in [User.Role.CEO, User.Role.HR]:
            return Response({"detail": "Only CEO and HR can create leave requests."}, status=status.HTTP_403_FORBIDDEN)

        employee_id = request.data.get('employee')
        leave_type = request.data.get('type', LeaveRequest.Type.VACATION)
        from_date_raw = request.data.get('from_date')
        to_date_raw = request.data.get('to_date')
        reason = request.data.get('reason', '')

        if not employee_id or not from_date_raw or not to_date_raw:
            return Response({'detail': 'employee, from_date and to_date are required.'}, status=status.HTTP_400_BAD_REQUEST)

        employee = get_object_or_404(User.objects.select_related('department'), id=employee_id)

        try:
            from_date_value = date.fromisoformat(from_date_raw)
            to_date_value = date.fromisoformat(to_date_raw)
        except ValueError:
            return Response({'detail': 'Invalid date format. Use YYYY-MM-DD.'}, status=status.HTTP_400_BAD_REQUEST)

        leave_request = LeaveRequest.objects.create(
            employee=employee,
            department=employee.department,
            type=leave_type,
            from_date=from_date_value,
            to_date=to_date_value,
            reason=reason,
            status=LeaveRequest.Status.PENDING,
        )

        return Response(
            {
                'id': leave_request.id,
                'employee': leave_request.employee_id,
                'type': leave_request.type,
                'from_date': leave_request.from_date.isoformat(),
                'to_date': leave_request.to_date.isoformat(),
                'status': leave_request.status,
            },
            status=status.HTTP_201_CREATED,
        )


class LeaveRequestApproveView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, id):
        if request.user.role not in [User.Role.CEO, User.Role.HR]:
            return Response({"detail": "Only CEO and HR can approve leave requests."}, status=status.HTTP_403_FORBIDDEN)

        leave_request = get_object_or_404(LeaveRequest, id=id)
        leave_request.status = LeaveRequest.Status.APPROVED
        leave_request.approved_by = request.user
        leave_request.save(update_fields=['status', 'approved_by', 'updated_at'])

        return Response({'id': leave_request.id, 'status': leave_request.status}, status=status.HTTP_200_OK)


class LeaveRequestRejectView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, id):
        if request.user.role not in [User.Role.CEO, User.Role.HR]:
            return Response({"detail": "Only CEO and HR can reject leave requests."}, status=status.HTTP_403_FORBIDDEN)

        leave_request = get_object_or_404(LeaveRequest, id=id)
        leave_request.status = LeaveRequest.Status.REJECTED
        leave_request.approved_by = request.user
        leave_request.save(update_fields=['status', 'approved_by', 'updated_at'])

        return Response({'id': leave_request.id, 'status': leave_request.status}, status=status.HTTP_200_OK)


class ContractListView(APIView):
    permission_classes = [IsAuthenticated]

    @staticmethod
    def _computed_status(contract, today):
        if contract.end_date is None:
            return 'ACTIVE'
        if contract.end_date < today:
            return 'EXPIRED'
        if contract.end_date <= today + timedelta(days=30):
            return 'EXPIRING'
        return 'ACTIVE'

    def get(self, request):
        if request.user.role not in [User.Role.CEO, User.Role.HR]:
            return Response({"detail": "Only CEO and HR can view contracts."}, status=status.HTTP_403_FORBIDDEN)

        status_filter = (request.query_params.get('status') or '').strip().lower()
        today = timezone.localdate()

        contracts = Contract.objects.select_related('employee', 'department').all().order_by('id')
        rows = []
        for contract in contracts:
            computed_status = self._computed_status(contract, today)

            if status_filter == 'expiring' and computed_status != 'EXPIRING':
                continue

            rows.append(
                {
                    'id': contract.id,
                    'contract_number': contract.contract_number,
                    'employee': contract.employee_id,
                    'employee_name': (f'{contract.employee.first_name} {contract.employee.last_name}'.strip() or contract.employee.username),
                    'department': contract.department.name if contract.department else None,
                    'type': contract.type,
                    'start_date': contract.start_date.isoformat(),
                    'end_date': contract.end_date.isoformat() if contract.end_date else None,
                    'salary_ron': str(contract.salary_ron),
                    'status': computed_status,
                }
            )

        return Response({'contracts': rows}, status=status.HTTP_200_OK)


class PayrollListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role not in [User.Role.CEO, User.Role.HR]:
            return Response({"detail": "Only CEO and HR can view payroll."}, status=status.HTTP_403_FORBIDDEN)

        month_raw = request.query_params.get('month')
        if not month_raw:
            return Response({'detail': 'month query parameter is required (YYYY-MM).'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            month_start = date.fromisoformat(f'{month_raw}-01')
        except ValueError:
            return Response({'detail': 'Invalid month format. Use YYYY-MM.'}, status=status.HTTP_400_BAD_REQUEST)

        bonus_raw = request.query_params.get('bonus', '0')
        deductions_raw = request.query_params.get('deductions', '0')
        try:
            bonus_value = Decimal(str(bonus_raw))
            deductions_value = Decimal(str(deductions_raw))
        except (InvalidOperation, TypeError):
            return Response({'detail': 'bonus and deductions must be numeric values.'}, status=status.HTTP_400_BAD_REQUEST)

        entries = PayrollEntry.objects.select_related('employee').filter(
            month__year=month_start.year,
            month__month=month_start.month,
        ).order_by('id')

        rows = []
        for entry in entries:
            base = Decimal(entry.gross_salary_ron or 0)
            net = base + bonus_value - deductions_value

            rows.append(
                {
                    'id': entry.id,
                    'employee': entry.employee_id,
                    'employee_name': (f'{entry.employee.first_name} {entry.employee.last_name}'.strip() or entry.employee.username),
                    'month': month_start.isoformat(),
                    'base_salary_ron': str(base),
                    'bonus_ron': str(bonus_value),
                    'deductions_ron': str(deductions_value),
                    'net_salary_ron': str(net),
                }
            )

        return Response({'month': month_raw, 'payroll': rows}, status=status.HTTP_200_OK)


class SupplierListView(APIView):
    """Return list of suppliers (for frontend receive form)."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # allow inventory and CEO to list suppliers
        if getattr(request.user, 'role', None) not in [User.Role.INVENTORY, User.Role.CEO, User.Role.HR]:
            return Response({'detail': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

        qs = Supplier.objects.all().order_by('name')
        serializer = SupplierSerializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class InventoryProductsView(APIView):
    """Return products with optional status filters (LOW/OUT).

    Example: /api/inventory/products/?status=LOW&status=OUT
    """
    # allow public for demo; change to IsAuthenticated in production
    permission_classes = [AllowAny]

    def get(self, request):
        statuses = request.query_params.getlist('status')

        qs = Product.objects.all()

        # build list
        products = []
        for p in qs:
            stock = int(getattr(p, 'stock_count', 0) or 0)
            # some deployments may have a Product model without min_stock yet
            minimum = int(getattr(p, 'min_stock', 0) or 0)
            if stock <= 0:
                status_val = 'OUT'
            elif stock < minimum:
                status_val = 'LOW'
            else:
                status_val = 'OK'

            shortfall = minimum - stock

            products.append({
                'id': p.id,
                'name': p.name,
                'sku': p.sku,
                'category': p.category,
                'stock_count': stock,
                'min_stock': minimum,
                'unit_price_ron': p.unit_price_ron,
                'status': status_val,
                'shortfall': shortfall,
            })

        if statuses:
            statuses_up = [s.upper() for s in statuses]
            products = [pr for pr in products if pr['status'] in statuses_up]

        return Response(products, status=status.HTTP_200_OK)


class StockMovementCreateView(APIView):
    """Create inbound/outbound stock movement. POST only."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # List stock movements with pagination and filters
        if getattr(request.user, 'role', None) not in [User.Role.INVENTORY, User.Role.CEO]:
            return Response({'detail': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

        qs = StockMovement.objects.select_related('product', 'supplier', 'created_by').all().order_by('-created_at')

        # Filters: ?type=, ?product= (id or sku), ?date_from=YYYY-MM-DD, ?date_to=YYYY-MM-DD
        types = request.query_params.getlist('type')
        if types:
            types_up = [t.upper() for t in types if t]
            qs = qs.filter(movement_type__in=types_up)

        product = request.query_params.get('product')
        if product:
            if product.isdigit():
                qs = qs.filter(product_id=int(product))
            else:
                qs = qs.filter(product__sku=product)

        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        try:
            if date_from:
                df = date.fromisoformat(date_from)
                qs = qs.filter(created_at__date__gte=df)
            if date_to:
                dt = date.fromisoformat(date_to)
                qs = qs.filter(created_at__date__lte=dt)
        except Exception:
            # ignore parse errors and return unfiltered by date
            pass

        paginator = PageNumberPagination()
        paginator.page_size = 20
        paginated = paginator.paginate_queryset(qs, request)
        serializer = StockMovementSerializer(paginated, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        # Only inventory role allowed
        if getattr(request.user, 'role', None) not in [User.Role.INVENTORY, User.Role.CEO]:
            return Response({'detail': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

        serializer = StockMovementSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        movement = serializer.save()

        # Return created movement and updated product data
        product = movement.product
        product_data = ProductSerializer(product).data

        return Response({'movement': StockMovementSerializer(movement).data, 'product': product_data}, status=status.HTTP_201_CREATED)


class DashboardItView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role not in [User.Role.CEO, User.Role.IT]:
            return Response({
                "detail": "Access denied. Only IT and CEO can view this dashboard."}, status=status.HTTP_403_FORBIDDEN
            )
        
        now = timezone.now()
        start_of_week = now - timedelta(days=now.weekday())
        start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)

        base_stats = Ticket.objects.aggregate(
            open_ticket=Count('id', filter=Q(status=Ticket.Status.OPEN)),
            in_progress=Count('id', filter=Q(status=Ticket.Status.IN_PROGRESS)),
            resolved_this_week=Count('id', filter=Q(
                status=Ticket.Status.RESOLVED,
                resolved_at__gte=start_of_week
            )),
            critical_open=Count('id', filter=Q(
                status=Ticket.Status.OPEN,
                priority__in=[Ticket.Priority.HIGH, Ticket.Priority.URGENT]
            ))
        )

        resolved_qs = Ticket.objects.filter(
            status=Ticket.Status.RESOLVED,
            resolved_at__gte=start_of_week
        ).annotate(
            duration=ExpressionWrapper(
                F('resolved_at') - F('created_at'),
                output_field=DurationField()
            )
        )

        perf_metrics = resolved_qs.aggregate(
            avg_res_time=Avg('duration'),
            sla_met_count=Count('id', filter=Q(duration__lte=timedelta(hours=4))),
        )

        avg_hrs = 0
        if perf_metrics['avg_res_time']:
            avg_hrs = round(perf_metrics['avg_res_time'].total_seconds() / 3600, 2)

        sla_pct = 0
        total_resolved = base_stats['resolved_this_week']
        if total_resolved > 0:
            sla_pct = round((perf_metrics['sla_met_count'] / total_resolved) * 100, 2)

        return Response({
            "open_ticket": base_stats['open_ticket'],
            "in_progress": base_stats['in_progress'],
            "resolved_this_week": total_resolved,
            "ceo_it_summary": {
                "avg_resolution_time_hrs": avg_hrs,
                "sla_met_percentage": sla_pct,
                "critical_open": base_stats['critical_open'],
            }
        }, status=status.HTTP_200_OK)


class ItTicketTrendView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role not in [User.Role.CEO, User.Role.IT]:
            return Response(
                {"detail": "Access denied. Only IT and CEO can view ticket trends."},
                status=status.HTTP_403_FORBIDDEN,
            )

        now = timezone.now()
        current_week_start = now - timedelta(days=now.weekday())
        current_week_start = current_week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        window_start = current_week_start - timedelta(weeks=5)
        window_end = current_week_start + timedelta(weeks=1)

        opened_rows = (
            Ticket.objects.filter(created_at__gte=window_start, created_at__lt=window_end)
            .annotate(week=TruncWeek('created_at'))
            .values('week')
            .annotate(opened_count=Count('id'))
            .order_by('week')
        )

        closed_rows = (
            Ticket.objects.filter(
                resolved_at__isnull=False,
                resolved_at__gte=window_start,
                resolved_at__lt=window_end,
            )
            .annotate(week=TruncWeek('resolved_at'))
            .values('week')
            .annotate(closed_count=Count('id'))
            .order_by('week')
        )

        opened_by_week = {
            row['week'].date().isoformat(): row['opened_count']
            for row in opened_rows
        }
        closed_by_week = {
            row['week'].date().isoformat(): row['closed_count']
            for row in closed_rows
        }

        weeks = []
        for week_index in range(6):
            week_start = window_start + timedelta(weeks=week_index)
            week_key = week_start.date().isoformat()
            weeks.append(
                {
                    'week_start': week_key,
                    'opened_count': opened_by_week.get(week_key, 0),
                    'closed_count': closed_by_week.get(week_key, 0),
                }
            )

        return Response({'weeks': weeks}, status=status.HTTP_200_OK)



class TicketPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 10

    def get_paginated_response(self, data):
        return Response(
            OrderedDict(
                [
                    ('total_count', self.page.paginator.count),
                    ('count', self.page.paginator.count),
                    ('next', self.get_next_link()),
                    ('previous', self.get_previous_link()),
                    ('results', data),
                ]
            )
        )


class OrderPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 10

    def get_paginated_response(self, data, total_ron_sum):
        return Response(
            OrderedDict(
                [
                    ('total_count', self.page.paginator.count),
                    ('total_ron_sum', str(total_ron_sum)),
                    ('count', self.page.paginator.count),
                    ('next', self.get_next_link()),
                    ('previous', self.get_previous_link()),
                    ('results', data),
                ]
            )
        )


class InvoicePagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 10

    def get_paginated_response(self, data):
        return Response(
            OrderedDict(
                [
                    ('total_count', self.page.paginator.count),
                    ('count', self.page.paginator.count),
                    ('next', self.get_next_link()),
                    ('previous', self.get_previous_link()),
                    ('results', data),
                ]
            )
        )


class TicketFilterSet(filters.FilterSet):
    search = filters.CharFilter(method='filter_search')
    category = filters.CharFilter(method='filter_category')
    status = filters.CharFilter(field_name='status')
    assigned_to = filters.CharFilter(method='filter_assigned_to')

    class Meta:
        model = Ticket
        fields = ['search', 'category', 'status', 'assigned_to']

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(title__icontains=value)
            | Q(description__icontains=value)
            | Q(ticket_number__icontains=value)
        )

    def filter_category(self, queryset, name, value):
        if value.isdigit():
            return queryset.filter(department_id=int(value))

        return queryset.filter(
            Q(department__name__iexact=value)
            | Q(department__slug__iexact=value)
        )

    def filter_assigned_to(self, queryset, name, value):
        request = getattr(self, 'request', None)
        if value == 'me' and request and request.user and request.user.is_authenticated:
            return queryset.filter(assigned_to=request.user)

        if value.isdigit():
            return queryset.filter(assigned_to_id=int(value))

        return queryset.none()


class TicketListCreateView(ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TicketSerializer
    pagination_class = TicketPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = TicketFilterSet

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return TicketCreateSerializer
        return TicketSerializer

    def get_queryset(self):
        request = self.request
        if request.user.role not in [User.Role.IT, User.Role.CEO]:
            raise PermissionDenied("Only IT technicians and CEO can view tickets.")

        return Ticket.objects.select_related(
            'department', 'requested_by', 'assigned_to', 'requested_for'
        ).all().order_by('-created_at')

    def create(self, request, *args, **kwargs):
        """Allow any authenticated user to create a ticket"""
        return super().create(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        # call parent to get paginated response
        response = super().list(request, *args, **kwargs)

        assigned_to = request.query_params.get('assigned_to')
        if assigned_to == 'me' and request.user and request.user.is_authenticated:
            base_qs = Ticket.objects.filter(assigned_to=request.user)
            in_progress_count = base_qs.filter(status=Ticket.Status.IN_PROGRESS).count()
            assigned_count = base_qs.count()
            resolved_count = base_qs.filter(status=Ticket.Status.RESOLVED).count()

            # attach a technician summary to the response payload
            try:
                # response.data is a dict-like from DRF
                response.data['technician_summary'] = {
                    'in_progress_count': in_progress_count,
                    'assigned_count': assigned_count,
                    'resolved_count': resolved_count,
                }
            except Exception:
                # best-effort: if response.data isn't mutable, skip
                pass

        return response


class TicketDetailView(RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TicketUpdateSerializer
    http_method_names = ['patch']
    lookup_field = 'id'

    def get_queryset(self):
        return Ticket.objects.select_related('department', 'requested_by', 'assigned_to').all()

    def patch(self, request, *args, **kwargs):
        if request.user.role not in [User.Role.IT, User.Role.CEO]:
            raise PermissionDenied('Only IT technicians and CEO can update tickets.')
        return self.partial_update(request, *args, **kwargs)
      
      
class OrderListView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.role not in [User.Role.SALES, User.Role.CEO]:
            return Response({"detail": "Only Sales and CEO can create orders."}, status=status.HTTP_403_FORBIDDEN)

        serializer = OrderCreateSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        response_serializer = OrderDetailSerializer(
            Order.objects.select_related('customer', 'created_by').prefetch_related('items__product').get(id=order.id)
        )
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    def get(self, request):
        if request.user.role not in [User.Role.SALES, User.Role.CEO]:
            return Response({"detail": "Only Sales and CEO can view orders."}, status=status.HTTP_403_FORBIDDEN)

        queryset = Order.objects.select_related('customer').all().order_by('-date', '-id')

        search = request.query_params.get('search', '').strip()
        if search:
            queryset = queryset.filter(
                Q(order_number__icontains=search) |
                Q(customer__name__icontains=search)
            )

        status_filter = request.query_params.get('status', '').strip()
        if status_filter:
            queryset = queryset.filter(status__iexact=status_filter)

        channel_filter = request.query_params.get('channel', '').strip()
        if channel_filter:
            queryset = queryset.filter(channel__iexact=channel_filter)

        totals = queryset.aggregate(total_ron_sum=Sum('value_ron'))
        total_ron_sum = totals['total_ron_sum'] or 0

        paginator = OrderPagination()
        paginated = paginator.paginate_queryset(queryset, request)
        serializer = OrderListSerializer(paginated, many=True)
        return paginator.get_paginated_response(serializer.data, total_ron_sum)


class OrderDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        if request.user.role not in [User.Role.SALES, User.Role.CEO]:
            return Response({"detail": "Only Sales and CEO can view orders."}, status=status.HTTP_403_FORBIDDEN)

        order = get_object_or_404(
            Order.objects.select_related('customer', 'created_by').prefetch_related('items__product'),
            id=id,
        )
        serializer = OrderDetailSerializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SalesDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    @staticmethod
    def _pct_change(today_value, yesterday_value):
        today_numeric = float(today_value or 0)
        yesterday_numeric = float(yesterday_value or 0)

        if yesterday_numeric == 0:
            return 100.0 if today_numeric > 0 else 0.0

        return round(((today_numeric - yesterday_numeric) / yesterday_numeric) * 100, 2)

    def get(self, request):
        if request.user.role not in [User.Role.SALES, User.Role.CEO]:
            return Response({"detail": "Only Sales and CEO can view sales KPI dashboard."}, status=status.HTTP_403_FORBIDDEN)

        today = timezone.localdate()
        yesterday = today - timedelta(days=1)
        start_of_week = today - timedelta(days=today.weekday())

        base_queryset = Order.objects.all()

        today_stats = base_queryset.filter(date=today).aggregate(
            orders_today=Count('id'),
            revenue_today_ron=Sum('value_ron'),
        )

        yesterday_stats = base_queryset.filter(date=yesterday).aggregate(
            orders_yesterday=Count('id'),
            revenue_yesterday_ron=Sum('value_ron'),
        )

        pending_orders = base_queryset.filter(status=Order.Status.PENDING).aggregate(count=Count('id'))['count'] or 0

        returns_this_week = base_queryset.filter(
            status=Order.Status.RETURNED,
            date__gte=start_of_week,
            date__lte=today,
        ).aggregate(count=Count('id'))['count'] or 0

        orders_today = today_stats['orders_today'] or 0
        revenue_today_ron = today_stats['revenue_today_ron'] or 0
        orders_yesterday = yesterday_stats['orders_yesterday'] or 0
        revenue_yesterday_ron = yesterday_stats['revenue_yesterday_ron'] or 0

        data = {
            'orders_today': orders_today,
            'revenue_today_ron': str(revenue_today_ron),
            'pending_orders': pending_orders,
            'returns_this_week': returns_this_week,
            'pct_changes': {
                'orders': self._pct_change(orders_today, orders_yesterday),
                'revenue': self._pct_change(revenue_today_ron, revenue_yesterday_ron),
            },
        }
        return Response(data, status=status.HTTP_200_OK)


class SalesDailyOrdersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role not in [User.Role.SALES, User.Role.CEO]:
            return Response({"detail": "Only Sales and CEO can view daily orders analytics."}, status=status.HTTP_403_FORBIDDEN)

        today = timezone.localdate()
        start_date = today - timedelta(days=6)

        aggregated = (
            Order.objects.filter(date__gte=start_date, date__lte=today)
            .annotate(day=TruncDay('date'))
            .values('day')
            .annotate(orders_count=Count('id'))
            .order_by('day')
        )

        by_day = {}
        for row in aggregated:
            day_value = row['day']
            if hasattr(day_value, 'date'):
                day_value = day_value.date()
            by_day[day_value.isoformat()] = row['orders_count']

        days = []
        for index in range(7):
            current_day = start_date + timedelta(days=index)
            day_key = current_day.isoformat()
            days.append({
                'date': day_key,
                'orders_count': by_day.get(day_key, 0),
            })

        return Response({'days': days}, status=status.HTTP_200_OK)


class SalesTopProductsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role not in [User.Role.SALES, User.Role.CEO]:
            return Response({"detail": "Only Sales and CEO can view top products analytics."}, status=status.HTTP_403_FORBIDDEN)

        today = timezone.localdate()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)

        products = (
            OrderItem.objects
            .annotate(order_day=TruncDay('order__date'))
            .filter(order__date__gte=week_start, order__date__lte=week_end)
            .values('product', 'product__name', 'product__sku')
            .annotate(
                units_sold=Sum('quantity'),
                order_lines=Count('id'),
                selling_days=Count('order_day', distinct=True),
            )
            .order_by('-units_sold', 'product__name')[:5]
        )

        data = [
            {
                'product_id': row['product'],
                'product_name': row['product__name'],
                'product_sku': row['product__sku'],
                'units_sold': row['units_sold'] or 0,
            }
            for row in products
        ]

        return Response(
            {
                'week_start': week_start.isoformat(),
                'week_end': week_end.isoformat(),
                'products': data,
            },
            status=status.HTTP_200_OK,
        )


class InventoryDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role not in [User.Role.INVENTORY, User.Role.CEO]:
            return Response({"detail": "Only Inventory Managers and CEO can view this dashboard."}, status=status.HTTP_403_FORBIDDEN)

        total_products = Product.objects.count()
        low_stock_count = Product.objects.filter(stock_count__lt=F('min_stock'), stock_count__gt=0).count()
        out_of_stock_count = Product.objects.filter(stock_count=0).count()
        deliveries_today = StockMovement.objects.filter(
            movement_type=StockMovement.Type.INBOUND,
            expected_date=date.today()
        ).count()

        return Response({
            "total_products": total_products,
            "low_stock_count": low_stock_count,
            "out_of_stock_count": out_of_stock_count,
            "deliveries_today": deliveries_today
        }, status=status.HTTP_200_OK)
class CustomerListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role not in [User.Role.SALES, User.Role.CEO]:
            return Response({"detail": "Only Sales and CEO can view customers."}, status=status.HTTP_403_FORBIDDEN)

        customers = (
            Customer.objects
            .annotate(total_value_ron=Coalesce(Sum('orders__value_ron'), Value(0), output_field=DecimalField(max_digits=12, decimal_places=2)))
            .order_by('-total_value_ron', 'name')
        )

        serializer = CustomerSalesSummarySerializer(customers, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class InvoiceListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role not in [User.Role.SALES, User.Role.CEO]:
            return Response({"detail": "Only Sales and CEO can view invoices."}, status=status.HTTP_403_FORBIDDEN)

        today = timezone.localdate()
        queryset = Invoice.objects.select_related('order', 'order__customer').all().order_by('-issued_date', '-id')

        status_filter = request.query_params.get('status', '').strip().upper()
        if status_filter:
            if status_filter == 'OVERDUE':
                queryset = queryset.filter(due_date__lt=today).exclude(status=Invoice.Status.PAID)
            else:
                queryset = queryset.filter(status__iexact=status_filter)

        paginator = InvoicePagination()
        paginated = paginator.paginate_queryset(queryset, request)
        serializer = InvoiceListSerializer(paginated, many=True)
        return paginator.get_paginated_response(serializer.data)


class SalesChannelSplitView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role not in [User.Role.SALES, User.Role.CEO]:
            return Response({"detail": "Only Sales and CEO can view channel split analytics."}, status=status.HTTP_403_FORBIDDEN)

        rows = (
            Order.objects
            .values('channel')
            .annotate(orders_count=Count('id'))
            .order_by('channel')
        )
        total_orders = sum(row['orders_count'] for row in rows)

        channels = []
        running_pct = 0.0
        for index, row in enumerate(rows):
            if total_orders == 0:
                pct = 0.0
            elif index == len(rows) - 1:
                pct = round(100.0 - running_pct, 2)
            else:
                pct = round((row['orders_count'] / total_orders) * 100, 2)
                running_pct += pct

            channels.append(
                {
                    'channel': row['channel'],
                    'orders_count': row['orders_count'],
                    'percentage': pct,
                }
            )

        return Response({'channels': channels}, status=status.HTTP_200_OK)


class SalesRevenueTrendView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role not in [User.Role.SALES, User.Role.CEO]:
            return Response({"detail": "Only Sales and CEO can view revenue trend analytics."}, status=status.HTTP_403_FORBIDDEN)

        today = timezone.localdate()
        start_date = today - timedelta(days=6)

        rows = []
        for index in range(7):
            current_day = start_date + timedelta(days=index)
            try:
                prior_year_day = current_day.replace(year=current_day.year - 1)
            except ValueError:
                prior_year_day = current_day - timedelta(days=365)

            current_total = Order.objects.filter(date=current_day).aggregate(total=Sum('value_ron'))['total'] or 0
            prior_year_total = Order.objects.filter(date=prior_year_day).aggregate(total=Sum('value_ron'))['total'] or 0

            rows.append(
                {
                    'date': current_day.isoformat(),
                    'current_year': str(current_total),
                    'prior_year': str(prior_year_total),
                }
            )

        return Response({'days': rows}, status=status.HTTP_200_OK)


class ReportListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        reports = Report.objects.all().order_by('-generated_at')
        category = request.query_params.get('category')
        if category:
            reports = reports.filter(category=category)
        return Response(ReportSerializer(reports, many=True).data)


class ReportDownloadView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        from pathlib import Path
        report = get_object_or_404(Report, id=id)
        if not report.file_path:
            return Response({'detail': 'File not available.'}, status=status.HTTP_404_NOT_FOUND)
        path = Path(report.file_path)
        if not path.exists():
            return Response({'detail': 'File not found on server.'}, status=status.HTTP_404_NOT_FOUND)
        return FileResponse(open(path, 'rb'), content_type='text/csv', as_attachment=True, filename=path.name)


class ReportGenerateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, slug):
        from .report_utils import generate_report_file
        if request.user.role != User.Role.CEO and not request.user.is_staff:
            raise PermissionDenied('Only CEO or admin can generate reports.')
        report = get_object_or_404(Report, slug=slug)
        generate_report_file(report, user=request.user)
        return Response(ReportSerializer(report).data, status=status.HTTP_200_OK)


class SystemStatusListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Only CEO and IT can view system status
        if request.user.role not in [User.Role.CEO, User.Role.IT]:
            raise PermissionDenied('Only CEO or IT team can view system status.')
        
        systems = SystemStatus.objects.all()
        serializer = SystemStatusSerializer(systems, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
