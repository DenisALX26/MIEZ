from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone
from model_bakery import baker
from rest_framework.test import APIClient

from api.models import Customer, Invoice, Order, Product, User


pytestmark = pytest.mark.django_db


def _authed_sales_client():
    user = baker.make(
        User,
        role=User.Role.SALES,
        username='sales_test_user',
        email='sales_test_user@example.com',
    )
    client = APIClient()
    client.force_authenticate(user=user)
    return client, user


def _prior_year_day(day):
    try:
        return day.replace(year=day.year - 1)
    except ValueError:
        return day - timedelta(days=365)


def test_post_orders_valid_payload_creates_invoice_via_signal():
    client, _ = _authed_sales_client()
    customer = baker.make(Customer)

    payload = {
        'customer': customer.id,
        'value_ron': '123.45',
        'date': timezone.localdate().isoformat(),
        'status': Order.Status.PENDING,
        'channel': Order.Channel.EMAG,
        'notes': 'Created from pytest',
    }

    response = client.post('/api/orders/', payload, format='json')

    assert response.status_code == 201
    order_id = response.data['id']
    order = Order.objects.get(id=order_id)

    invoice = Invoice.objects.get(order=order)
    assert invoice.amount_ron == Decimal('123.45')
    assert invoice.invoice_number.startswith('INV-')


def test_get_orders_returns_paginated_list_with_total_ron_sum():
    client, user = _authed_sales_client()
    customer = baker.make(Customer)

    baker.make(Order, customer=customer, created_by=user, value_ron=Decimal('10.00'))
    baker.make(Order, customer=customer, created_by=user, value_ron=Decimal('20.00'))
    baker.make(Order, customer=customer, created_by=user, value_ron=Decimal('5.00'))

    response = client.get('/api/orders/?page_size=2')

    assert response.status_code == 200
    assert response.data['total_count'] == 3
    assert Decimal(response.data['total_ron_sum']) == Decimal('35.00')
    assert len(response.data['results']) == 2


def test_get_orders_with_status_pending_filters_correctly():
    client, user = _authed_sales_client()
    customer = baker.make(Customer)

    baker.make(Order, customer=customer, created_by=user, status=Order.Status.PENDING)
    baker.make(Order, customer=customer, created_by=user, status=Order.Status.SHIPPED)

    response = client.get('/api/orders/?status=Pending')

    assert response.status_code == 200
    assert response.data['total_count'] == 1
    assert all(item['status'] == Order.Status.PENDING for item in response.data['results'])


def test_get_orders_with_channel_emag_filters_correctly():
    client, user = _authed_sales_client()
    customer = baker.make(Customer)

    baker.make(Order, customer=customer, created_by=user, channel=Order.Channel.EMAG)
    baker.make(Order, customer=customer, created_by=user, channel=Order.Channel.WEBSITE)

    response = client.get('/api/orders/?channel=eMAG')

    assert response.status_code == 200
    assert response.data['total_count'] == 1
    assert all(item['channel'] == Order.Channel.EMAG for item in response.data['results'])


def test_get_customers_sorted_by_total_value_desc_with_annotation():
    client, user = _authed_sales_client()

    customer_a = baker.make(Customer, name='Alpha')
    customer_b = baker.make(Customer, name='Beta')

    baker.make(Order, customer=customer_a, created_by=user, value_ron=Decimal('100.00'))
    baker.make(Order, customer=customer_a, created_by=user, value_ron=Decimal('50.00'))
    baker.make(Order, customer=customer_b, created_by=user, value_ron=Decimal('40.00'))

    response = client.get('/api/customers/')

    assert response.status_code == 200
    assert response.data[0]['name'] == 'Alpha'
    assert Decimal(response.data[0]['total_value_ron']) == Decimal('150.00')
    assert response.data[1]['name'] == 'Beta'
    assert Decimal(response.data[1]['total_value_ron']) == Decimal('40.00')


def test_get_invoices_computes_overdue_status_correctly():
    client, user = _authed_sales_client()
    customer = baker.make(Customer)
    today = timezone.localdate()

    overdue_order = baker.make(Order, customer=customer, created_by=user, value_ron=Decimal('10.00'))
    paid_order = baker.make(Order, customer=customer, created_by=user, value_ron=Decimal('20.00'))
    future_order = baker.make(Order, customer=customer, created_by=user, value_ron=Decimal('30.00'))

    overdue_invoice = baker.make(
        Invoice,
        order=overdue_order,
        invoice_number='INV-90001',
        amount_ron=Decimal('10.00'),
        due_date=today - timedelta(days=1),
        status=Invoice.Status.ISSUED,
    )
    paid_invoice = baker.make(
        Invoice,
        order=paid_order,
        invoice_number='INV-90002',
        amount_ron=Decimal('20.00'),
        due_date=today - timedelta(days=2),
        status=Invoice.Status.PAID,
    )
    future_invoice = baker.make(
        Invoice,
        order=future_order,
        invoice_number='INV-90003',
        amount_ron=Decimal('30.00'),
        due_date=today + timedelta(days=2),
        status=Invoice.Status.ISSUED,
    )

    response = client.get('/api/invoices/?page_size=20')

    assert response.status_code == 200
    by_number = {row['invoice_number']: row for row in response.data['results']}

    assert by_number[overdue_invoice.invoice_number]['effective_status'] == 'OVERDUE'
    assert by_number[paid_invoice.invoice_number]['effective_status'] == Invoice.Status.PAID
    assert by_number[future_invoice.invoice_number]['effective_status'] == Invoice.Status.ISSUED


def test_get_invoices_status_overdue_returns_only_overdue():
    client, user = _authed_sales_client()
    customer = baker.make(Customer)
    today = timezone.localdate()

    overdue_order = baker.make(Order, customer=customer, created_by=user)
    non_overdue_order = baker.make(Order, customer=customer, created_by=user)

    baker.make(
        Invoice,
        order=overdue_order,
        invoice_number='INV-91001',
        due_date=today - timedelta(days=1),
        status=Invoice.Status.ISSUED,
    )
    baker.make(
        Invoice,
        order=non_overdue_order,
        invoice_number='INV-91002',
        due_date=today + timedelta(days=1),
        status=Invoice.Status.ISSUED,
    )

    response = client.get('/api/invoices/?status=Overdue&page_size=20')

    assert response.status_code == 200
    assert response.data['total_count'] == 1
    assert all(row['effective_status'] == 'OVERDUE' for row in response.data['results'])


def test_product_availability_mapping_for_stock_thresholds():
    out = baker.make(Product, stock_count=0)
    low = baker.make(Product, stock_count=5)
    in_stock = baker.make(Product, stock_count=10)

    assert out.availability == 'Out of Stock'
    assert low.availability == 'Low Stock'
    assert in_stock.availability == 'In Stock'


def test_get_sales_channel_split_percentages_sum_to_100():
    client, user = _authed_sales_client()
    customer = baker.make(Customer)

    baker.make(Order, customer=customer, created_by=user, channel=Order.Channel.EMAG)
    baker.make(Order, customer=customer, created_by=user, channel=Order.Channel.EMAG)
    baker.make(Order, customer=customer, created_by=user, channel=Order.Channel.WEBSITE)
    baker.make(Order, customer=customer, created_by=user, channel=Order.Channel.DIRECT)

    response = client.get('/api/sales/channel-split/')

    assert response.status_code == 200
    total_pct = sum(float(item['percentage']) for item in response.data['channels'])
    assert round(total_pct, 2) == 100.0


def test_get_sales_revenue_trend_returns_7_entries_with_current_and_prior_year_values():
    client, user = _authed_sales_client()
    customer = baker.make(Customer)

    today = timezone.localdate()
    prior_year_today = _prior_year_day(today)

    baker.make(Order, customer=customer, created_by=user, date=today, value_ron=Decimal('75.00'))
    baker.make(Order, customer=customer, created_by=user, date=prior_year_today, value_ron=Decimal('50.00'))

    response = client.get('/api/sales/revenue-trend/')

    assert response.status_code == 200
    assert 'days' in response.data
    assert len(response.data['days']) == 7
    assert all(
        {'date', 'current_year', 'prior_year'}.issubset(entry.keys())
        for entry in response.data['days']
    )

    today_row = next((entry for entry in response.data['days'] if entry['date'] == today.isoformat()), None)
    assert today_row is not None
    assert Decimal(today_row['current_year']) == Decimal('75.00')
    assert Decimal(today_row['prior_year']) == Decimal('50.00')
