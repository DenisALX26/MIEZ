from datetime import timedelta

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Invoice, Order, Ticket


@receiver(post_save, sender=Order)
def create_invoice_for_new_order(sender, instance, created, **kwargs):
    if not created:
        return

    if Invoice.objects.filter(order=instance).exists():
        return

    last_number = (
        Invoice.objects.filter(invoice_number__startswith='INV-')
        .order_by('-id')
        .values_list('invoice_number', flat=True)
        .first()
    )

    next_number = 1
    if last_number and last_number.startswith('INV-'):
        raw = last_number.split('INV-', 1)[1]
        if raw.isdigit():
            next_number = int(raw) + 1

    Invoice.objects.create(
        invoice_number=f'INV-{next_number:05d}',
        order=instance,
        issued_by=instance.created_by,
        amount_ron=instance.value_ron,
        due_date=instance.date + timedelta(days=7),
        status=Invoice.Status.ISSUED,
    )


# ── Workflow event triggers ───────────────────────────────────────────────────

def _fire_workflows(trigger_type: str, context: dict) -> None:
    from .models import Workflow
    from .workflow_engine import execute_workflow
    for workflow in Workflow.objects.filter(trigger_type=trigger_type, is_active=True):
        execute_workflow(workflow, trigger_type, context)


@receiver(post_save, sender=Order)
def trigger_new_order_workflows(sender, instance, created, **kwargs):
    if not created:
        return
    context = {
        'order_id': instance.id,
        'order_number': str(instance.order_number),
        'value_ron': float(instance.value_ron or 0),
        'message': f'New order {instance.order_number} received.',
        'link': '/sales',
    }
    _fire_workflows('NEW_ORDER_RECEIVED', context)


@receiver(post_save, sender=Order)
def trigger_order_threshold_workflows(sender, instance, created, **kwargs):
    if not created:
        return
    from .models import Workflow
    from .workflow_engine import execute_workflow
    for workflow in Workflow.objects.filter(trigger_type='ORDER_EXCEEDS_THRESHOLD', is_active=True):
        threshold = float(workflow.trigger_config.get('threshold', 10000))
        if float(instance.value_ron or 0) >= threshold:
            context = {
                'order_id': instance.id,
                'order_number': str(instance.order_number),
                'value_ron': float(instance.value_ron),
                'threshold': threshold,
                'message': f'Order {instance.order_number} of {instance.value_ron} RON exceeds threshold of {threshold} RON.',
                'link': '/sales',
            }
            execute_workflow(workflow, 'ORDER_EXCEEDS_THRESHOLD', context)


@receiver(post_save, sender=Ticket)
def trigger_new_ticket_workflows(sender, instance, created, **kwargs):
    if not created:
        return
    context = {
        'ticket_id': instance.id,
        'title': instance.title,
        'priority': instance.priority,
        'message': f'New IT ticket #{instance.id}: {instance.title} (priority: {instance.priority}).',
        'link': '/it',
    }
    _fire_workflows('NEW_IT_TICKET', context)


