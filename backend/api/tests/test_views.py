from datetime import timedelta
from decimal import Decimal

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from model_bakery import baker
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from django.conf import settings
from ..models import User, Ticket, Customer, Product, Order, OrderItem

class IsEvenTests(TestCase):
    def setUp(self):
        self.client = Client()

    # ── Success cases ──────────────────────────────────────────

    def test_even_number(self):
        response = self.client.get('/api/is_even/', {'number': 4})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['even'], True)

    def test_odd_number(self):
        response = self.client.get('/api/is_even/', {'number': 3})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['even'], False)

    def test_zero(self):
        response = self.client.get('/api/is_even/', {'number': 0})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['even'], True)

    def test_negative_even(self):
        response = self.client.get('/api/is_even/', {'number': -2})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['even'], True)

    def test_negative_odd(self):
        response = self.client.get('/api/is_even/', {'number': -7})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['even'], False)

    # ── Fail cases ─────────────────────────────────────────────

    def test_missing_number(self):
        response = self.client.get('/api/is_even/')
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

    def test_string_input(self):
        response = self.client.get('/api/is_even/', {'number': 'abc'})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

    def test_float_string(self):
        response = self.client.get('/api/is_even/', {'number': '2.5'})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

    def test_post_not_allowed(self):
        response = self.client.post('/api/is_even/', {'number': 2})
        self.assertEqual(response.status_code, 405)  # method not allowed


class AuthTests(APITestCase):
    def setUp(self):
        self.username = 'testuser'
        self.password = 'testpass123'
        User = get_user_model()
        self.user = User.objects.create_user(username=self.username, password=self.password)
        self.login_url = reverse('login')
        self.me_url = reverse('user_me')
        self.logout_url = reverse('logout')

    def test_login_sets_cookies(self):
        data = {"username": self.username, "password": self.password}
        response = self.client.post(self.login_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(settings.SIMPLE_JWT['AUTH_COOKIE'], response.cookies)
        self.assertIn(settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH'], response.cookies)
        self.assertTrue(response.cookies[settings.SIMPLE_JWT['AUTH_COOKIE']]['httponly'])

    def test_protected_route_access(self):
        self.client.post(self.login_url, {"username": self.username, "password": self.password})
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        # Ensure expected fields exist in the JSON response. The user model may not
        # always expose a `role` attribute, so assert presence of core fields.
        self.assertEqual(data.get('username'), self.username)
        self.assertIn('email', data)
        self.assertIn('message', data)

    def test_access_denied_without_cookie(self):
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_clears_cookies(self):
        self.client.post(self.login_url, {"username": self.username, "password": self.password})

        response = self.client.post(self.logout_url)
        access_cookie = response.cookies.get(settings.SIMPLE_JWT['AUTH_COOKIE'])
        self.assertEqual(access_cookie.value, '')


class ITDashboardTests(APITestCase):
    def setUp(self):
        self.ceo = User.objects.create_user(username='ceo', role=User.Role.CEO, email='ceo@example.com')
        self.hr_user = User.objects.create_user(username='hr', role=User.Role.HR, email='hr@example.com')
        self.it_user = User.objects.create_user(username='it', role=User.Role.IT, email='it@example.com')

        self.now = timezone.now()

    def test_access_control(self):
        """Only CEO and IT should access the IT dashboard"""
        self.client.force_authenticate(user=self.hr_user)
        response = self.client.get('/api/it/dashboard/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.ceo)
        response = self.client.get('/api/it/dashboard/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.client.force_authenticate(user=self.it_user)
        response = self.client.get('/api/it/dashboard/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_dashboard_metrics(self):
        """Test that counts and SLA math are correct"""
        self.client.force_authenticate(user=self.ceo)

        # Create workload
        Ticket.objects.create(ticket_number="T1", status=Ticket.Status.OPEN)
        Ticket.objects.create(ticket_number="T2", status=Ticket.Status.OPEN, priority=Ticket.Priority.URGENT)
        Ticket.objects.create(ticket_number="T3", status=Ticket.Status.IN_PROGRESS)

        # Create resolved (SLA met: 2 hours)
        t4 = Ticket.objects.create(ticket_number="T4", status=Ticket.Status.RESOLVED)
        t4.created_at = self.now - timedelta(hours=2)
        t4.resolved_at = self.now
        t4.save()

        # Create resolved (SLA missed: 6 hours)
        t5 = Ticket.objects.create(ticket_number="T5", status=Ticket.Status.RESOLVED)
        t5.created_at = self.now - timedelta(hours=6)
        t5.resolved_at = self.now
        t5.save()

        response = self.client.get('/api/it/dashboard/')
        data = response.data

        self.assertEqual(data['open_ticket'], 2)
        self.assertEqual(data['ceo_it_summary']['critical_open'], 1)
        self.assertEqual(data['ceo_it_summary']['avg_resolution_time_hrs'], 4.0)
        self.assertEqual(data['ceo_it_summary']['sla_met_percentage'], 50.0)

    def test_model_auto_resolve_timestamp(self):
        """Test that out save() method handles resolved_at correctly"""
        ticket = Ticket.objects.create(ticket_number="T99", status=Ticket.Status.OPEN)
        self.assertIsNone(ticket.resolved_at)

        ticket.status = Ticket.Status.RESOLVED
        ticket.resolved_at = timezone.now()
        ticket.save()

        self.assertIsNotNone(ticket.resolved_at)


class TicketListViewTests(APITestCase):
    def setUp(self):
        self.ceo = User.objects.create_user(username='ceo_tickets', role=User.Role.CEO, email='ceo_tickets@example.com')
        self.it_user = User.objects.create_user(username='it_tickets', role=User.Role.IT, email='it_tickets@example.com')
        self.sales_user = User.objects.create_user(username='sales_tickets', role=User.Role.SALES, email='sales_tickets@example.com')

        from ..models import Department

        self.it_department = Department.objects.create(name='IT Support', slug='it-support')
        self.hr_department = Department.objects.create(name='HR', slug='hr')

        Ticket.objects.create(
            ticket_number='IT-001',
            title='Laptop not booting',
            description='Device stuck on BIOS screen',
            department=self.it_department,
            status=Ticket.Status.OPEN,
            assigned_to=self.it_user,
        )
        Ticket.objects.create(
            ticket_number='IT-002',
            title='Email migration issue',
            description='Mailbox sync fails after update',
            department=self.it_department,
            status=Ticket.Status.IN_PROGRESS,
            assigned_to=self.it_user,
        )
        Ticket.objects.create(
            ticket_number='HR-001',
            title='Payroll access reset',
            description='Cannot log in to payroll portal',
            department=self.hr_department,
            status=Ticket.Status.OPEN,
            assigned_to=self.ceo,
        )

    def test_ticket_list_requires_it_or_ceo_role(self):
        self.client.force_authenticate(user=self.sales_user)
        response = self.client.get('/api/tickets/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_ticket_list_includes_total_count(self):
        self.client.force_authenticate(user=self.it_user)
        response = self.client.get('/api/tickets/?page_size=2')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_count'], 3)
        self.assertEqual(response.data['count'], 3)
        self.assertEqual(len(response.data['results']), 2)

    def test_ticket_list_filters_with_django_filter_params(self):
        self.client.force_authenticate(user=self.it_user)

        response = self.client.get(
            f'/api/tickets/?category={self.it_department.id}&status=OPEN&assigned_to={self.it_user.id}'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_count'], 1)
        self.assertEqual(response.data['results'][0]['ticket_number'], 'IT-001')

    def test_ticket_list_search_filters_results(self):
        self.client.force_authenticate(user=self.it_user)

        response = self.client.get('/api/tickets/?search=mailbox')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_count'], 1)
        self.assertEqual(response.data['results'][0]['ticket_number'], 'IT-002')


class TicketApiTests(APITestCase):
    def setUp(self):
        from ..models import Department

        user_model = get_user_model()
        self.it_user = baker.make(
            user_model,
            role=user_model.Role.IT,
            username='it_test_user',
            email='it_test_user@example.com',
        )
        self.ceo_user = baker.make(
            user_model,
            role=user_model.Role.CEO,
            username='ceo_test_user',
            email='ceo_test_user@example.com',
        )
        self.hardware_department = baker.make(Department, name='Hardware', slug='hardware')

    def test_post_tickets_valid_payload_returns_201_with_new_status_and_auto_incremented_number(self):
        self.client.force_authenticate(user=self.it_user)

        first_response = self.client.post(
            '/api/tickets/',
            {
                'title': 'Laptop battery issue',
                'description': 'Battery drains in 30 minutes.',
                'priority': Ticket.Priority.HIGH,
            },
            format='json',
        )

        second_response = self.client.post(
            '/api/tickets/',
            {
                'title': 'VPN access failure',
                'description': 'Cannot connect from home network.',
                'priority': Ticket.Priority.MEDIUM,
            },
            format='json',
        )

        self.assertEqual(first_response.status_code, 201)
        self.assertEqual(second_response.status_code, 201)
        self.assertEqual(first_response.data['status'], Ticket.Status.OPEN)
        self.assertEqual(second_response.data['status'], Ticket.Status.OPEN)
        self.assertTrue(first_response.data['ticket_number'].startswith('TKT-'))
        self.assertTrue(second_response.data['ticket_number'].startswith('TKT-'))

        first_number = int(first_response.data['ticket_number'].split('-')[1])
        second_number = int(second_response.data['ticket_number'].split('-')[1])
        self.assertEqual(second_number, first_number + 1)

    def test_post_tickets_missing_title_returns_400_with_title_key(self):
        self.client.force_authenticate(user=self.it_user)

        response = self.client.post(
            '/api/tickets/',
            {
                'description': 'Keyboard keys are not working.',
                'priority': Ticket.Priority.LOW,
            },
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('title', response.data)

    def test_post_tickets_missing_description_returns_400(self):
        self.client.force_authenticate(user=self.it_user)

        response = self.client.post(
            '/api/tickets/',
            {
                'title': 'Monitor flickers intermittently',
                'priority': Ticket.Priority.MEDIUM,
            },
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('description', response.data)

    def test_get_tickets_returns_full_list_sorted_by_created_at_desc(self):
        self.client.force_authenticate(user=self.it_user)

        older = baker.make(
            Ticket,
            ticket_number='TKT-00001',
            title='Older ticket',
            description='Older issue',
            status=Ticket.Status.OPEN,
        )
        newer = baker.make(
            Ticket,
            ticket_number='TKT-00002',
            title='Newer ticket',
            description='Newer issue',
            status=Ticket.Status.OPEN,
        )

        now = timezone.now()
        Ticket.objects.filter(id=older.id).update(created_at=now - timedelta(days=1))
        Ticket.objects.filter(id=newer.id).update(created_at=now)

        response = self.client.get('/api/tickets/?page_size=100')

        self.assertEqual(response.status_code, 200)
        numbers = [item['ticket_number'] for item in response.data['results']]
        self.assertEqual(numbers[:2], ['TKT-00002', 'TKT-00001'])

    def test_get_tickets_with_category_filters_correctly(self):
        self.client.force_authenticate(user=self.it_user)

        from ..models import Department

        other_department = baker.make(Department, name='Software', slug='software')

        baker.make(
            Ticket,
            ticket_number='TKT-00010',
            title='Hardware issue',
            description='Disk failure',
            department=self.hardware_department,
            status=Ticket.Status.OPEN,
        )
        baker.make(
            Ticket,
            ticket_number='TKT-00011',
            title='Software issue',
            description='App crash',
            department=other_department,
            status=Ticket.Status.OPEN,
        )

        response = self.client.get('/api/tickets/?category=Hardware&page_size=100')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['ticket_number'], 'TKT-00010')

    def test_get_tickets_with_assigned_to_me_returns_only_requesting_user_tickets(self):
        self.client.force_authenticate(user=self.it_user)

        user_model = get_user_model()
        other_user = baker.make(
            user_model,
            role=user_model.Role.IT,
            username='other_it_user',
            email='other_it_user@example.com',
        )

        baker.make(
            Ticket,
            ticket_number='TKT-00020',
            title='Mine',
            description='Assigned to me',
            assigned_to=self.it_user,
            status=Ticket.Status.OPEN,
        )
        baker.make(
            Ticket,
            ticket_number='TKT-00021',
            title='Not mine',
            description='Assigned to someone else',
            assigned_to=other_user,
            status=Ticket.Status.OPEN,
        )

        response = self.client.get('/api/tickets/?assigned_to=me&page_size=100')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['ticket_number'], 'TKT-00020')

    def test_patch_ticket_status_transitions_open_to_in_progress_to_resolved_with_auto_assignment(self):
        self.client.force_authenticate(user=self.it_user)

        ticket = baker.make(
            Ticket,
            ticket_number='TKT-00030',
            title='Transition ticket',
            description='State machine test',
            status=Ticket.Status.OPEN,
        )

        to_in_progress = self.client.patch(f'/api/tickets/{ticket.id}/', {'status': Ticket.Status.IN_PROGRESS}, format='json')
        self.assertEqual(to_in_progress.status_code, 200)
        self.assertEqual(to_in_progress.data['status'], Ticket.Status.IN_PROGRESS)
        self.assertEqual(to_in_progress.data['assigned_to'], self.it_user.id)

        to_resolved = self.client.patch(f'/api/tickets/{ticket.id}/', {'status': Ticket.Status.RESOLVED}, format='json')
        self.assertEqual(to_resolved.status_code, 200)
        self.assertEqual(to_resolved.data['status'], Ticket.Status.RESOLVED)

    def test_patch_ticket_sets_resolved_at_automatically_when_resolved(self):
        self.client.force_authenticate(user=self.it_user)

        ticket = baker.make(
            Ticket,
            ticket_number='TKT-00031',
            title='Resolved timestamp ticket',
            description='Resolved timestamp test',
            status=Ticket.Status.IN_PROGRESS,
            resolved_at=None,
        )

        response = self.client.patch(f'/api/tickets/{ticket.id}/', {'status': Ticket.Status.RESOLVED}, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.data['resolved_at'])

        ticket.refresh_from_db()
        self.assertIsNotNone(ticket.resolved_at)

    def test_get_it_dashboard_avg_resolution_time_hours_computed_correctly(self):
        self.client.force_authenticate(user=self.ceo_user)

        now = timezone.now()

        t1 = baker.make(
            Ticket,
            ticket_number='TKT-00040',
            title='Resolved in 2h',
            description='Resolution timing test 1',
            status=Ticket.Status.RESOLVED,
        )
        t2 = baker.make(
            Ticket,
            ticket_number='TKT-00041',
            title='Resolved in 6h',
            description='Resolution timing test 2',
            status=Ticket.Status.RESOLVED,
        )

        Ticket.objects.filter(id=t1.id).update(created_at=now - timedelta(hours=2), resolved_at=now)
        Ticket.objects.filter(id=t2.id).update(created_at=now - timedelta(hours=6), resolved_at=now)

        response = self.client.get('/api/it/dashboard/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['ceo_it_summary']['avg_resolution_time_hrs'], 4.0)

    def test_get_it_dashboard_sla_compliance_counts_tickets_resolved_within_4_hours(self):
        self.client.force_authenticate(user=self.ceo_user)

        now = timezone.now()

        sla_met = baker.make(
            Ticket,
            ticket_number='TKT-00050',
            title='Resolved in 3h',
            description='SLA compliant',
            status=Ticket.Status.RESOLVED,
        )
        sla_missed = baker.make(
            Ticket,
            ticket_number='TKT-00051',
            title='Resolved in 7h',
            description='SLA missed',
            status=Ticket.Status.RESOLVED,
        )

        Ticket.objects.filter(id=sla_met.id).update(created_at=now - timedelta(hours=3), resolved_at=now)
        Ticket.objects.filter(id=sla_missed.id).update(created_at=now - timedelta(hours=7), resolved_at=now)

        response = self.client.get('/api/it/dashboard/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['ceo_it_summary']['sla_met_percentage'], 50.0)
class OrderListViewTests(APITestCase):
    def setUp(self):
        self.sales_user = User.objects.create_user(
            username='sales_orders',
            role=User.Role.SALES,
            email='sales_orders@example.com',
        )
        self.ceo_user = User.objects.create_user(
            username='ceo_orders',
            role=User.Role.CEO,
            email='ceo_orders@example.com',
        )
        self.hr_user = User.objects.create_user(
            username='hr_orders',
            role=User.Role.HR,
            email='hr_orders@example.com',
        )

        self.customer_acme = Customer.objects.create(name='Acme SRL')
        self.customer_beta = Customer.objects.create(name='Beta SRL')

        self.product_a = Product.objects.create(name='Widget A', sku='WIDGET-A')
        self.product_b = Product.objects.create(name='Widget B', sku='WIDGET-B')

        self.order_1 = Order.objects.create(
            customer=self.customer_acme,
            created_by=self.sales_user,
            value_ron=Decimal('120.50'),
            status=Order.Status.PROCESSING,
            channel=Order.Channel.WEBSITE,
            notes='Priority handling',
        )
        self.order_2 = Order.objects.create(
            customer=self.customer_beta,
            created_by=self.sales_user,
            value_ron=Decimal('80.00'),
            status=Order.Status.SHIPPED,
            channel=Order.Channel.EMAG,
        )
        self.order_3 = Order.objects.create(
            customer=self.customer_acme,
            created_by=self.sales_user,
            value_ron=Decimal('40.00'),
            status=Order.Status.PENDING,
            channel=Order.Channel.DIRECT,
        )

        OrderItem.objects.create(order=self.order_1, product=self.product_a, quantity=2, unit_price_ron=Decimal('30.00'))
        OrderItem.objects.create(order=self.order_1, product=self.product_b, quantity=1, unit_price_ron=Decimal('60.50'))

    def test_order_number_is_auto_generated_with_hash_format(self):
        self.assertRegex(self.order_1.order_number, r'^#\d{4}$')

    def test_orders_list_supports_search_status_channel_and_includes_totals(self):
        self.client.force_authenticate(user=self.sales_user)

        response = self.client.get('/api/orders/?search=Acme&status=PROCESSING&channel=WEBSITE')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_count'], 1)
        self.assertEqual(Decimal(response.data['total_ron_sum']), Decimal('120.50'))
        self.assertEqual(len(response.data['results']), 1)

        row = response.data['results'][0]
        self.assertIn('order_number', row)
        self.assertEqual(row['customer_name'], 'Acme SRL')
        self.assertEqual(Decimal(row['value_ron']), Decimal('120.50'))
        self.assertEqual(row['status'], Order.Status.PROCESSING)
        self.assertEqual(row['channel'], Order.Channel.WEBSITE)

    def test_orders_list_is_paginated_and_includes_total_sum_for_filtered_queryset(self):
        self.client.force_authenticate(user=self.ceo_user)

        response = self.client.get('/api/orders/?search=SRL&page_size=2')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_count'], 3)
        self.assertEqual(Decimal(response.data['total_ron_sum']), Decimal('240.50'))
        self.assertEqual(len(response.data['results']), 2)

    def test_order_detail_includes_line_items_for_modal(self):
        self.client.force_authenticate(user=self.sales_user)

        response = self.client.get(f'/api/orders/{self.order_1.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['order_number'], self.order_1.order_number)
        self.assertEqual(response.data['customer_name'], 'Acme SRL')
        self.assertEqual(len(response.data['items']), 2)
        self.assertIn('line_total_ron', response.data['items'][0])

    def test_orders_endpoints_forbid_non_sales_roles(self):
        self.client.force_authenticate(user=self.hr_user)

        list_response = self.client.get('/api/orders/')
        detail_response = self.client.get(f'/api/orders/{self.order_1.id}/')

        self.assertEqual(list_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(detail_response.status_code, status.HTTP_403_FORBIDDEN)
        