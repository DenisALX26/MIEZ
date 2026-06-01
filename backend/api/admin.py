from django.contrib import admin
from .models import Product, Supplier, StockMovement, Order, Customer, Department, Ticket, Workflow, WorkflowLog

admin.site.register(Supplier)
admin.site.register(Product)
admin.site.register(StockMovement)
admin.site.register(Order)
admin.site.register(Customer)
admin.site.register(Department)
admin.site.register(Ticket)

#test comment
@admin.register(Workflow)
class WorkflowAdmin(admin.ModelAdmin):
    list_display = ('name', 'trigger_type', 'is_active', 'updated_at')
    list_editable = ('is_active',)
    list_filter = ('is_active',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(WorkflowLog)
class WorkflowLogAdmin(admin.ModelAdmin):
    list_display = ('workflow', 'triggered_at', 'trigger_type', 'success')
    list_filter = ('workflow', 'success', 'trigger_type')
    readonly_fields = ('workflow', 'triggered_at', 'trigger_type', 'actions_log', 'success')

    def has_add_permission(self, request):
        return False
