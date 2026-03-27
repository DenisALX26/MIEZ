from django.urls import path
from . import views
from .views import LoginView, RefreshTokenView


urlpatterns = [
  path('is_even/', views.is_even, name='is_even'),
  path('auth/login/', LoginView.as_view(), name='login'),
  path('auth/refresh/', RefreshTokenView.as_view(), name='refresh'),
  path('auth/logout/', views.LogoutView.as_view(), name='logout'),
  path('auth/me/', views.UserMeView.as_view(), name='user_me'),
  path('employees/', views.EmployeeListView.as_view(), name='employee_list'),
  path('employees/stats/', views.EmployeeStatsView.as_view(), name='employee_stats'),
]