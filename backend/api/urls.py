from django.urls import path, include
from . import views
from .views import LoginView, RefreshTokenView, LoginView


urlpatterns = [
  path('is_even/', views.is_even, name='is_even'),
  # Add your app urls here, for example:
  # path('myapp/', include('myapp.urls')),
  path('auth/login/', LoginView.as_view(), name='login'),
  path('auth/refresh/', RefreshTokenView.as_view(), name='refresh'),
  path('auth/logout/', views.LogoutView.as_view(), name='logout'),
  path('auth/me/', views.UserMeView.as_view(), name='user_me'),
]