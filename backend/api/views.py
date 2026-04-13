from datetime import timedelta
from collections import OrderedDict

from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.shortcuts import get_object_or_404
from django.db.models import F, Avg, Count, Q, DurationField, ExpressionWrapper, Sum
from django.utils import timezone

from django.conf import settings
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import PermissionDenied
from django_filters import rest_framework as filters
from django_filters.rest_framework import DjangoFilterBackend

from .models import Department, Supplier, User, Product, StockMovement, Ticket, Order
from .serializers import (
    DepartmentSerializer,
    EmployeeCreateSerializer,
    EmployeeListSerializer,
    OrderDetailSerializer,
    OrderListSerializer,
    ProductSerializer,
    SupplierSerializer,
    StockMovementSerializer,
    TicketSerializer,
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
        # List recent stock movements (inventory + CEO allowed)
        if getattr(request.user, 'role', None) not in [User.Role.INVENTORY, User.Role.CEO]:
            return Response({'detail': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

        qs = StockMovement.objects.select_related('product', 'supplier').all().order_by('-created_at')[:100]
        serializer = StockMovementSerializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

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



class TicketPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

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
    max_page_size = 100

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


class TicketFilterSet(filters.FilterSet):
    search = filters.CharFilter(method='filter_search')
    category = filters.NumberFilter(field_name='department_id')
    status = filters.CharFilter(field_name='status')
    assigned_to = filters.NumberFilter(field_name='assigned_to_id')

    class Meta:
        model = Ticket
        fields = ['search', 'category', 'status', 'assigned_to']

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(title__icontains=value)
            | Q(description__icontains=value)
            | Q(ticket_number__icontains=value)
        )


class TicketListView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TicketSerializer
    pagination_class = TicketPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = TicketFilterSet

    def get_queryset(self):
        request = self.request
        if request.user.role not in [User.Role.IT, User.Role.CEO]:
            raise PermissionDenied("Only IT technicians and CEO can view tickets.")

        return Ticket.objects.select_related(
            'department', 'requested_by', 'assigned_to'
        ).all().order_by('-created_at')


class OrderListView(APIView):
    permission_classes = [IsAuthenticated]

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
