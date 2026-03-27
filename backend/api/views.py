from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.shortcuts import get_object_or_404
from django.db.models import Count, Q

from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination

from .models import Department, User
from .serializers import DepartmentSerializer, EmployeeListSerializer


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
        departments = Department.objects.all()
        serializer = DepartmentSerializer(departments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        if request.user.role != 'CEO':
            return Response({"detail": "Only CEOs can create departments."}, status=status.HTTP_403_FORBIDDEN)

        serializer = DepartmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class DepartmentDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, id):
        if request.user.role != 'CEO':
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


class EmployeeStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
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
