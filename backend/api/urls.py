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
  path('inventory/dashboard/', views.InventoryDashboardView.as_view(), name='inventory_dashboard_kpis'),
  path('inventory/suppliers/', views.SupplierListView.as_view(), name='supplier_list'),
  path('inventory/stock-movements/', views.StockMovementCreateView.as_view(), name='stock_movements'),
  path('departments/', views.DepartmentListCreateView.as_view(), name='department_list_create'),
  path('departments/<int:id>/', views.DepartmentDeleteView.as_view(), name='department_delete'),
  path('employees/', views.EmployeeListView.as_view(), name='employee_list'),
  path('employees/stats/', views.EmployeeStatsView.as_view(), name='employee_stats'),
  path('hr/dashboard/', views.HrDashboardView.as_view(), name='hr_dashboard_kpis'),
  path('hr/ceo-summary/', views.CeoHrSummaryView.as_view(), name='ceo_hr_summary'),
  path('sales/dashboard/', views.SalesDashboardView.as_view(), name='sales_dashboard_kpis'),
  path('sales/daily-orders/', views.SalesDailyOrdersView.as_view(), name='sales_daily_orders'),
  path('sales/top-products/', views.SalesTopProductsView.as_view(), name='sales_top_products'),
  path('sales/channel-split/', views.SalesChannelSplitView.as_view(), name='sales_channel_split'),
  path('sales/revenue-trend/', views.SalesRevenueTrendView.as_view(), name='sales_revenue_trend'),
  path('customers/', views.CustomerListView.as_view(), name='customer_list'),
  path('invoices/', views.InvoiceListView.as_view(), name='invoice_list'),
  path('orders/', views.OrderListView.as_view(), name='order_list'),
  path('orders/<int:id>/', views.OrderDetailView.as_view(), name='order_detail'),
  path('it/dashboard/', views.DashboardItView.as_view(), name='dashboard_data'),
  path('it/ticket-trend/', views.ItTicketTrendView.as_view(), name='it_ticket_trend'),
  path('tickets/', views.TicketListCreateView.as_view(), name='ticket_list'),
  path('tickets/<int:id>/', views.TicketDetailView.as_view(), name='ticket_detail'),
]
