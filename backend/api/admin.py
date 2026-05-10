from django.contrib import admin
from .models import Product, Supplier, StockMovement, Order, Customer, Department, Ticket, Workflow, WorkflowLog

admin.site.register(Supplier)
admin.site.register(Product)
admin.site.register(StockMovement)
admin.site.register(Order)
admin.site.register(Customer)
admin.site.register(Department)
admin.site.register(Ticket)


@admin.register(Workflow)
class WorkflowAdmin(admin.ModelAdmin):
    list_display = ('name', 'trigger_type', 'is_active', 'updated_at')
    list_editable = ('is_active',)
    list_filter = ('is_active',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(WorkflowLog)
class WorkflowLogAdmin(admin.ModelAdmin):
    list_display = ('workflow', 'triggered_at', 'status_display', 'error_message')
    list_filter = ('workflow',)
    readonly_fields = ('workflow', 'triggered_at', 'trigger_input', 'trigger_result', 'error_message')

    def status_display(self, obj):
        return obj.trigger_result.get('status', '—') if obj.trigger_result else '—'
    status_display.short_description = 'Status'

    def has_add_permission(self, request):
        return False
