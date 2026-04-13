from datetime import timedelta

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Invoice, Order


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
