"""
Tests for DEV-134: workflow endpoints + engine.

Covers:
- POST /api/workflows/ — create (valid, missing name, empty actions, invalid trigger)
- GET /api/workflows/ — list with active count
- PATCH /api/workflows/{id}/toggle/ — flips is_active
- DELETE /api/workflows/{id}/ — 204 and removed
- GET /api/workflows/triggers/ — registry
- GET /api/workflows/actions/ — registry
- GET /api/workflows/logs/ — CEO-only
- WorkflowLog created on execution
- Failed action logs error and continues to next action
- Event-based triggers fire via Django signals (order, ticket, stock)
- Time-based triggers fire via run_workflows management command
"""
from django.test import TestCase
from rest_framework.test import APIClient

from api.models import Notification, User, Workflow, WorkflowLog
from api.workflow_engine import execute_workflow


def _ceo(**kw):
    name = kw.get('username', 'ceo')
    return User.objects.create_user(username=name, email=f'{name}@test.com', password='pass', role='CEO')


def _hr(**kw):
    name = kw.get('username', 'hr')
    return User.objects.create_user(username=name, email=f'{name}@test.com', password='pass', role='HR')


def _it(**kw):
    name = kw.get('username', 'it')
    return User.objects.create_user(username=name, email=f'{name}@test.com', password='pass', role='IT')


def _workflow(**kw):
    return Workflow.objects.create(
        name=kw.get('name', 'Test Workflow'),
        trigger_type=kw.get('trigger_type', 'DAILY_AT_TIME'),
        trigger_config=kw.get('trigger_config', {'time': '08:00'}),
        actions=kw.get('actions', ['NOTIFY_MANAGER']),
        is_active=kw.get('is_active', True),
    )


VALID_PAYLOAD = {
    'name': 'New Order Alert',
    'trigger_type': 'NEW_ORDER_RECEIVED',
    'trigger_config': {},
    'actions': ['NOTIFY_MANAGER', 'EMAIL_CEO'],
    'is_active': True,
}


class WorkflowCreateTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.ceo = _ceo()
        self.client.force_authenticate(user=self.ceo)

    def test_create_workflow_returns_201(self):
        res = self.client.post('/api/workflows/', VALID_PAYLOAD, format='json')
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.data['name'], 'New Order Alert')
        self.assertTrue(Workflow.objects.filter(name='New Order Alert').exists())

    def test_create_workflow_missing_name_returns_400(self):
        payload = {**VALID_PAYLOAD, 'name': ''}
        res = self.client.post('/api/workflows/', payload, format='json')
        self.assertEqual(res.status_code, 400)

    def test_create_workflow_empty_actions_returns_400(self):
        payload = {**VALID_PAYLOAD, 'actions': []}
        res = self.client.post('/api/workflows/', payload, format='json')
        self.assertEqual(res.status_code, 400)

    def test_create_workflow_invalid_trigger_type_returns_400(self):
        payload = {**VALID_PAYLOAD, 'trigger_type': 'NOT_A_REAL_TRIGGER'}
        res = self.client.post('/api/workflows/', payload, format='json')
        self.assertEqual(res.status_code, 400)

    def test_create_workflow_forbidden_for_non_ceo_hr(self):
        self.client.force_authenticate(user=_it(username='it1'))
        res = self.client.post('/api/workflows/', VALID_PAYLOAD, format='json')
        self.assertEqual(res.status_code, 403)


class WorkflowListTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.ceo = _ceo()
        self.client.force_authenticate(user=self.ceo)
        _workflow(name='W1', is_active=True)
        _workflow(name='W2', is_active=True)
        _workflow(name='W3', is_active=False)

    def test_list_workflows_returns_correct_active_count(self):
        res = self.client.get('/api/workflows/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 3)
        active = [w for w in res.data if w['is_active']]
        self.assertEqual(len(active), 2)

    def test_list_includes_trigger_and_action_labels(self):
        res = self.client.get('/api/workflows/')
        self.assertEqual(res.status_code, 200)
        w = res.data[0]
        self.assertIn('trigger_label', w)
        self.assertIn('action_labels', w)


class WorkflowToggleTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.ceo = _ceo()
        self.client.force_authenticate(user=self.ceo)
        self.workflow = _workflow(is_active=True)

    def test_toggle_workflow_flips_is_active_to_false(self):
        res = self.client.patch(
            f'/api/workflows/{self.workflow.id}/toggle/',
            {'is_active': False},
            format='json',
        )
        self.assertEqual(res.status_code, 200)
        self.workflow.refresh_from_db()
        self.assertFalse(self.workflow.is_active)

    def test_toggle_workflow_flips_is_active_to_true(self):
        self.workflow.is_active = False
        self.workflow.save()
        res = self.client.patch(
            f'/api/workflows/{self.workflow.id}/toggle/',
            {'is_active': True},
            format='json',
        )
        self.assertEqual(res.status_code, 200)
        self.workflow.refresh_from_db()
        self.assertTrue(self.workflow.is_active)

    def test_toggle_missing_is_active_returns_400(self):
        res = self.client.patch(f'/api/workflows/{self.workflow.id}/toggle/', {}, format='json')
        self.assertEqual(res.status_code, 400)


class WorkflowDeleteTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.ceo = _ceo()
        self.client.force_authenticate(user=self.ceo)
        self.workflow = _workflow()

    def test_delete_workflow_returns_204(self):
        wid = self.workflow.id
        res = self.client.delete(f'/api/workflows/{wid}/')
        self.assertEqual(res.status_code, 204)
        self.assertFalse(Workflow.objects.filter(id=wid).exists())

    def test_delete_nonexistent_returns_404(self):
        res = self.client.delete('/api/workflows/99999/')
        self.assertEqual(res.status_code, 404)


class WorkflowRegistryTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=_ceo(username='ceo2'))

    def test_triggers_endpoint_returns_all_types(self):
        res = self.client.get('/api/workflows/triggers/')
        self.assertEqual(res.status_code, 200)
        values = [t['value'] for t in res.data]
        self.assertIn('DAILY_AT_TIME', values)
        self.assertIn('NEW_ORDER_RECEIVED', values)
        self.assertIn('NEW_IT_TICKET', values)

    def test_actions_endpoint_returns_all_types(self):
        res = self.client.get('/api/workflows/actions/')
        self.assertEqual(res.status_code, 200)
        values = [a['value'] for a in res.data]
        self.assertIn('NOTIFY_MANAGER', values)
        self.assertIn('EMAIL_CEO', values)
        self.assertIn('LOG_TO_AUDIT_TRAIL', values)


class WorkflowLogTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.ceo = _ceo(username='ceo3')
        self.hr = _hr(username='hr1')
        self.workflow = _workflow()

    def test_workflow_log_created_on_execution(self):
        self.assertEqual(WorkflowLog.objects.count(), 0)
        execute_workflow(self.workflow, 'DAILY_AT_TIME', {
            'message': 'Test execution',
            'link': '/workflows',
        })
        self.assertEqual(WorkflowLog.objects.count(), 1)
        log = WorkflowLog.objects.first()
        self.assertEqual(log.workflow, self.workflow)
        self.assertEqual(log.trigger_type, 'DAILY_AT_TIME')
        self.assertTrue(log.success)

    def test_workflow_log_endpoint_ceo_only(self):
        execute_workflow(self.workflow, 'DAILY_AT_TIME', {'message': 'test', 'link': '/'})
        self.client.force_authenticate(user=self.ceo)
        res = self.client.get('/api/workflows/logs/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 1)

    def test_workflow_log_endpoint_forbidden_for_hr(self):
        self.client.force_authenticate(user=self.hr)
        res = self.client.get('/api/workflows/logs/')
        self.assertEqual(res.status_code, 403)


class WorkflowEngineTests(TestCase):
    def setUp(self):
        self.ceo = _ceo(username='ceo4')
        self.hr = _hr(username='hr2')
        self.workflow = _workflow(actions=['NOTIFY_MANAGER', 'EMAIL_CEO', 'LOG_TO_AUDIT_TRAIL'])

    def test_failed_action_logs_error_and_continues(self):
        """An action that throws must not stop subsequent actions."""
        from unittest.mock import patch

        def boom(*args, **kwargs):
            raise ValueError('simulated failure')

        with patch('api.workflow_engine._notify_manager', side_effect=boom):
            result = execute_workflow(self.workflow, 'DAILY_AT_TIME', {'message': 'x', 'link': '/'})

        self.assertFalse(result['success'])
        log = result['actions_log']
        # NOTIFY_MANAGER failed
        self.assertFalse(log[0]['success'])
        self.assertIn('simulated failure', log[0]['message'])
        # EMAIL_CEO still ran
        self.assertTrue(log[1]['success'])
        # LOG_TO_AUDIT_TRAIL still ran
        self.assertTrue(log[2]['success'])

    def test_engine_creates_notifications_for_managers(self):
        workflow = _workflow(actions=['NOTIFY_MANAGER'])
        before = Notification.objects.count()
        execute_workflow(workflow, 'DAILY_AT_TIME', {'message': 'alert', 'link': '/'})
        after = Notification.objects.count()
        # Should have created one notification per CEO/HR user
        managers = User.objects.filter(role__in=('HR', 'CEO')).count()
        self.assertEqual(after - before, managers)

    def test_engine_updates_last_triggered_at(self):
        self.assertIsNone(self.workflow.last_triggered_at)
        execute_workflow(self.workflow, 'DAILY_AT_TIME', {'message': 'x', 'link': '/'})
        self.workflow.refresh_from_db()
        self.assertIsNotNone(self.workflow.last_triggered_at)


# ── Helpers for signal / command tests ───────────────────────────────────────

def _customer():
    from api.models import Customer
    return Customer.objects.create(name='Test Customer')


def _sales_user():
    name = 'sales_trig'
    return User.objects.create_user(username=name, email=f'{name}@test.com', password='pass', role='SALES')


def _order(customer, created_by=None, value_ron=500):
    from api.models import Order
    return Order.objects.create(customer=customer, created_by=created_by, value_ron=value_ron)


def _ticket(requested_by):
    from api.models import Ticket
    return Ticket.objects.create(
        ticket_number=Ticket._generate_ticket_number(),
        title='Test issue',
        requested_by=requested_by,
    )


def _product(stock_count=20, min_stock=10):
    from api.models import Product
    return Product.objects.create(
        name='Widget', sku=f'SKU-{Product.objects.count()}',
        stock_count=stock_count, min_stock=min_stock,
    )


def _stock_movement(product, qty, movement_type='OUTBOUND'):
    from api.models import StockMovement
    return StockMovement.objects.create(
        product=product, movement_type=movement_type, quantity=qty,
    )


# ── Event-based trigger tests ─────────────────────────────────────────────────

class EventTriggerTests(TestCase):
    """Verify Django signals fire the workflow engine for event-based triggers."""

    def test_new_order_triggers_workflow(self):
        _workflow(name='Order Alert', trigger_type='NEW_ORDER_RECEIVED', actions=['NOTIFY_MANAGER'])
        customer = _customer()
        self.assertEqual(WorkflowLog.objects.count(), 0)
        _order(customer)
        self.assertEqual(WorkflowLog.objects.count(), 1)
        log = WorkflowLog.objects.first()
        self.assertEqual(log.trigger_type, 'NEW_ORDER_RECEIVED')
        self.assertTrue(log.success)

    def test_inactive_workflow_not_triggered_on_new_order(self):
        _workflow(name='Inactive Order', trigger_type='NEW_ORDER_RECEIVED', actions=['NOTIFY_MANAGER'], is_active=False)
        _order(_customer())
        self.assertEqual(WorkflowLog.objects.count(), 0)

    def test_new_order_above_threshold_triggers_workflow(self):
        _workflow(
            name='High Value Alert',
            trigger_type='ORDER_EXCEEDS_THRESHOLD',
            trigger_config={'threshold': 1000},
            actions=['EMAIL_CEO'],
        )
        customer = _customer()
        # Below threshold — should not trigger
        _order(customer, value_ron=500)
        self.assertEqual(WorkflowLog.objects.count(), 0)
        # Above threshold — should trigger
        _order(customer, value_ron=2000)
        self.assertEqual(WorkflowLog.objects.count(), 1)
        self.assertEqual(WorkflowLog.objects.first().trigger_type, 'ORDER_EXCEEDS_THRESHOLD')

    def test_new_it_ticket_triggers_workflow(self):
        _workflow(name='Ticket Alert', trigger_type='NEW_IT_TICKET', actions=['ASSIGN_TO_TEAM_LEAD'])
        user = _sales_user()
        self.assertEqual(WorkflowLog.objects.count(), 0)
        _ticket(user)
        self.assertEqual(WorkflowLog.objects.count(), 1)
        log = WorkflowLog.objects.first()
        self.assertEqual(log.trigger_type, 'NEW_IT_TICKET')

    def test_stock_below_minimum_triggers_workflow(self):
        _workflow(name='Low Stock Alert', trigger_type='STOCK_BELOW_MINIMUM', actions=['EMAIL_SUPPLIER'])
        product = _product(stock_count=15, min_stock=10)
        # OUTBOUND of 8 leaves stock_count=7, which is < min_stock=10
        _stock_movement(product, qty=8, movement_type='OUTBOUND')
        self.assertEqual(WorkflowLog.objects.count(), 1)
        log = WorkflowLog.objects.first()
        self.assertEqual(log.trigger_type, 'STOCK_BELOW_MINIMUM')

    def test_stock_above_minimum_does_not_trigger(self):
        _workflow(name='Low Stock Alert 2', trigger_type='STOCK_BELOW_MINIMUM', actions=['EMAIL_SUPPLIER'])
        product = _product(stock_count=15, min_stock=10)
        # OUTBOUND of 3 leaves stock_count=12, still above min_stock=10
        _stock_movement(product, qty=3, movement_type='OUTBOUND')
        self.assertEqual(WorkflowLog.objects.count(), 0)

    def test_multiple_workflows_all_triggered(self):
        _workflow(name='Alert A', trigger_type='NEW_ORDER_RECEIVED', actions=['NOTIFY_MANAGER'])
        _workflow(name='Alert B', trigger_type='NEW_ORDER_RECEIVED', actions=['EMAIL_CEO'])
        _order(_customer())
        self.assertEqual(WorkflowLog.objects.count(), 2)


# ── Time-based trigger tests (management command) ─────────────────────────────

class TimeTriggerTests(TestCase):
    """Verify run_workflows management command fires time-based triggers."""

    def _call(self, fake_now):
        from unittest.mock import patch
        from django.core.management import call_command
        with patch('api.management.commands.run_workflows.timezone.localtime', return_value=fake_now):
            call_command('run_workflows', verbosity=0)

    def _fake_now(self, weekday_name: str, time_str: str):
        """Return a mock datetime matching the given weekday name and HH:MM string."""
        import datetime
        from django.utils import timezone as tz
        # Build a real date for the requested weekday
        days = {'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
                'friday': 4, 'saturday': 5, 'sunday': 6}
        target_weekday = days[weekday_name]
        today = datetime.date.today()
        delta = (target_weekday - today.weekday()) % 7
        target_date = today + datetime.timedelta(days=delta)
        h, m = map(int, time_str.split(':'))
        dt = datetime.datetime(target_date.year, target_date.month, target_date.day, h, m,
                               tzinfo=tz.get_current_timezone())
        return dt

    def test_daily_at_time_triggers_at_scheduled_time(self):
        _workflow(
            name='Daily Standup',
            trigger_type='DAILY_AT_TIME',
            trigger_config={'time': '09:30'},
            actions=['NOTIFY_MANAGER'],
        )
        self._call(self._fake_now('monday', '09:30'))
        self.assertEqual(WorkflowLog.objects.count(), 1)
        self.assertEqual(WorkflowLog.objects.first().trigger_type, 'DAILY_AT_TIME')

    def test_daily_at_time_does_not_trigger_at_wrong_time(self):
        _workflow(
            name='Daily Check',
            trigger_type='DAILY_AT_TIME',
            trigger_config={'time': '09:30'},
            actions=['NOTIFY_MANAGER'],
        )
        self._call(self._fake_now('monday', '10:00'))
        self.assertEqual(WorkflowLog.objects.count(), 0)

    def test_weekly_at_time_triggers_on_correct_day_and_time(self):
        _workflow(
            name='Weekly Report',
            trigger_type='WEEKLY_AT_TIME',
            trigger_config={'day_of_week': 'wednesday', 'time': '08:00'},
            actions=['EMAIL_CEO'],
        )
        self._call(self._fake_now('wednesday', '08:00'))
        self.assertEqual(WorkflowLog.objects.count(), 1)
        self.assertEqual(WorkflowLog.objects.first().trigger_type, 'WEEKLY_AT_TIME')

    def test_weekly_at_time_does_not_trigger_on_wrong_day(self):
        _workflow(
            name='Weekly Check',
            trigger_type='WEEKLY_AT_TIME',
            trigger_config={'day_of_week': 'wednesday', 'time': '08:00'},
            actions=['EMAIL_CEO'],
        )
        self._call(self._fake_now('tuesday', '08:00'))
        self.assertEqual(WorkflowLog.objects.count(), 0)

    def test_inactive_workflow_not_triggered_by_command(self):
        _workflow(
            name='Inactive Daily',
            trigger_type='DAILY_AT_TIME',
            trigger_config={'time': '09:30'},
            actions=['NOTIFY_MANAGER'],
            is_active=False,
        )
        self._call(self._fake_now('monday', '09:30'))
        self.assertEqual(WorkflowLog.objects.count(), 0)

    def test_managed_by_workflow_skipped_by_command(self):
        """Workflows with managed_by in trigger_config are owned by dedicated commands."""
        _workflow(
            name='HR Agent',
            trigger_type='WEEKLY_AT_TIME',
            trigger_config={'day_of_week': 'monday', 'time': '06:00', 'managed_by': 'run_hr_agent'},
            actions=['GENERATE_REPORT'],
        )
        self._call(self._fake_now('monday', '06:00'))
        self.assertEqual(WorkflowLog.objects.count(), 0)
