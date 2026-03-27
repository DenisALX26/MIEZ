from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.shortcuts import get_object_or_404

from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .models import Department
from .serializers import DepartmentSerializer


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
