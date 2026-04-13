from django.contrib import admin
from .models import Product, Supplier, StockMovement, Order, Customer, Department, Ticket

admin.site.register(Supplier)
admin.site.register(Product)
admin.site.register(StockMovement)
admin.site.register(Order)
admin.site.register(Customer)
admin.site.register(Department)
admin.site.register(Ticket)
