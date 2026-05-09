"""Tests for assistant tool functions."""

from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from api.agent.operations import (
    create_leave_request,
    create_ticket,
    generate_report,
    get_dashboard_summary,
    query_employees,
    query_tickets,
)
from api.models import Customer, Department, LeaveRequest, Order, Product, Report, Ticket, User


class AssistantToolTests(TestCase):
    def setUp(self):
        self.department = Department.objects.create(name='Sales', slug='sales')
        self.hr_department = Department.objects.create(name='Human Resources', slug='hr')

        self.ceo = User.objects.create_user(username='ceo', email='ceo@example.com', role=User.Role.CEO)
        self.hr_user = User.objects.create_user(username='hr', email='hr@example.com', role=User.Role.HR, department=self.hr_department)
        self.sales_user = User.objects.create_user(username='sales', email='sales@example.com', role=User.Role.SALES, department=self.department)
        self.it_user = User.objects.create_user(username='it', email='it@example.com', role=User.Role.IT)

    def test_get_dashboard_summary_sales_returns_expected_keys(self):
        customer = Customer.objects.create(name='Acme Corp')
        today = timezone.localdate()
        yesterday = today - timedelta(days=1)

        Order.objects.create(
            customer=customer,
            created_by=self.sales_user,
            value_ron='100.00',
            date=today,
            status=Order.Status.PENDING,
        )
        Order.objects.create(
            customer=customer,
            created_by=self.sales_user,
            value_ron='50.00',
            date=yesterday,
            status=Order.Status.RETURNED,
        )

        summary = get_dashboard_summary(module='sales', user=self.sales_user)

        self.assertEqual(
            set(summary.keys()),
            {'orders_today', 'revenue_today_ron', 'pending_orders', 'returns_this_week', 'pct_changes'},
        )
        self.assertEqual(summary['orders_today'], 1)
        self.assertEqual(summary['revenue_today_ron'], '100.00')

    def test_get_dashboard_summary_hr_denied_for_sales_role(self):
        with self.assertRaises(PermissionError):
            get_dashboard_summary(module='hr', user=self.sales_user)

    def test_query_tickets_new_returns_only_open_tickets(self):
        ticket_one = Ticket.objects.create(ticket_number='TKT-00001', title='Printer issue', status=Ticket.Status.OPEN, requested_by=self.it_user)
        Ticket.objects.create(ticket_number='TKT-00002', title='Network issue', status=Ticket.Status.IN_PROGRESS, requested_by=self.it_user)

        results = query_tickets(status='NEW', user=self.it_user)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], ticket_one.id)
        self.assertTrue(all(item['status'] == 'NEW' for item in results))

    def test_query_employees_denied_for_sales_role(self):
        with self.assertRaises(PermissionError):
            query_employees(user=self.sales_user)

    def test_create_ticket_sets_requested_by_to_request_user(self):
        ticket = create_ticket(
            user=self.sales_user,
            title='Laptop replacement',
            description='Battery no longer holds charge',
            category='Hardware',
            location='HQ',
        )

        self.assertEqual(ticket.requested_by, self.sales_user)
        self.assertEqual(ticket.status, Ticket.Status.OPEN)

    def test_create_leave_request_sets_pending_status(self):
        employee = User.objects.create_user(
            username='employee',
            email='employee@example.com',
            role=User.Role.SALES,
            department=self.department,
        )

        leave_request = create_leave_request(
            user=self.hr_user,
            employee=employee,
            from_date=timezone.localdate() + timedelta(days=1),
            to_date=timezone.localdate() + timedelta(days=3),
            reason='Vacation',
        )

        self.assertEqual(leave_request.status, LeaveRequest.Status.PENDING)
        self.assertEqual(leave_request.employee_id, employee.id)

    def test_create_leave_request_denied_for_ceo(self):
        employee = User.objects.create_user(
            username='employee2',
            email='employee2@example.com',
            role=User.Role.SALES,
            department=self.department,
        )

        with self.assertRaises(PermissionError):
            create_leave_request(
                user=self.ceo,
                employee=employee,
                from_date=timezone.localdate() + timedelta(days=1),
                to_date=timezone.localdate() + timedelta(days=3),
                reason='Vacation',
            )

    def test_generate_report_denied_for_non_manager_role(self):
        report = Report.objects.create(
            name='Sales Report',
            slug='sales-report',
            category='Sales',
            period='May 2026',
        )

        with self.assertRaises(PermissionError):
            generate_report(user=self.sales_user, slug=report.slug)

    def test_generate_report_allowed_for_ceo_with_mocked_file_generation(self):
        report = Report.objects.create(
            name='Sales Report',
            slug='sales-report-2',
            category='Sales',
            period='May 2026',
        )

        with patch('api.agent.operations.generate_report_file') as mocked_generate:
            result = generate_report(user=self.ceo, slug=report.slug)

        mocked_generate.assert_called_once()
        self.assertEqual(result.id, report.id)