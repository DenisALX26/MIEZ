from django.urls import path
from . import views
from .views import LoginView, RefreshTokenView


urlpatterns = [
  path('is_even/', views.is_even, name='is_even'),
  path('auth/login/', LoginView.as_view(), name='login'),
  path('auth/refresh/', RefreshTokenView.as_view(), name='refresh'),
  path('auth/logout/', views.LogoutView.as_view(), name='logout'),
  path('auth/me/', views.UserMeView.as_view(), name='user_me'),
  path('inventory/products/', views.InventoryProductsView.as_view(), name='inventory_products'),
  path('inventory/suppliers/', views.SupplierListView.as_view(), name='supplier_list'),
  path('inventory/stock-movements/', views.StockMovementCreateView.as_view(), name='stock_movements'),
  path('departments/', views.DepartmentListCreateView.as_view(), name='department_list_create'),
  path('departments/<int:id>/', views.DepartmentDeleteView.as_view(), name='department_delete'),
  path('employees/', views.EmployeeListView.as_view(), name='employee_list'),
  path('employees/stats/', views.EmployeeStatsView.as_view(), name='employee_stats'),
  path('it/dashboard/', views.DashboardItView.as_view(), name='dashboard_data'),
]