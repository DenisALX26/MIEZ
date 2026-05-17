from datetime import timedelta
from decimal import Decimal

from django.utils import timezone
from model_bakery import baker
from rest_framework import status
from rest_framework.test import APITestCase

from api.models import Attendance, Contract, Department, LeaveRequest, PayrollEntry, User


class HrEndpointsTestCase(APITestCase):
    def setUp(self):
        self.hr_user = baker.make(
            User,
            role=User.Role.HR,
            username='hr_test_user',
            email='hr_test_user@example.com',
        )
        self.hr_client = APITestCase.client_class()
        self.hr_client.force_authenticate(user=self.hr_user)
        self.hr_department = baker.make(Department, name='Human Resources', slug='hr')


class TestHrEmployeesEndpoint(HrEndpointsTestCase):
    def test_get_employees_returns_full_list_with_expected_fields(self):
        baker.make(
            User,
            role=User.Role.SALES,
            department=self.hr_department,
            first_name='Ana',
            last_name='Pop',
            username='ana.pop',
            email='ana.pop@example.com',
            employment_type=User.EmploymentType.FULL_TIME,
            full_time=True,
            is_active=True,
        )
        baker.make(
            User,
            role=User.Role.IT,
            department=self.hr_department,
            first_name='Mihai',
            last_name='Ionescu',
            username='mihai.ionescu',
            email='mihai.ionescu@example.com',
            employment_type=User.EmploymentType.CONTRACTOR,
            full_time=False,
            is_active=False,
        )

        response = self.hr_client.get('/api/employees/?page_size=100')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data['count'], 2)
        self.assertGreaterEqual(len(response.data['results']), 2)

        first = response.data['results'][0]
        expected_keys = {
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'phone',
            'position',
            'employment_type',
            'start_date',
            'salary_ron',
            'address',
            'role',
            'is_active',
            'full_time',
            'department',
        }
        self.assertTrue(expected_keys.issubset(first.keys()))


class TestHrAttendanceEndpoint(HrEndpointsTestCase):
    def test_get_attendance_week_returns_expected_grid(self):
        today = timezone.localdate()
        week_start = today - timedelta(days=today.weekday())

        employee = baker.make(
            User,
            role=User.Role.SALES,
            department=self.hr_department,
            first_name='Elena',
            last_name='Vasilescu',
            username='elena.v',
        )

        baker.make(Attendance, employee=employee, date=week_start, status=Attendance.Status.PRESENT)
        baker.make(Attendance, employee=employee, date=week_start + timedelta(days=1), status=Attendance.Status.REMOTE)

        response = self.hr_client.get(f'/api/attendance/?week={week_start.isoformat()}')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['week_start'], week_start.isoformat())
        self.assertEqual(len(response.data['days']), 7)

        row = next(item for item in response.data['grid'] if item['employee_id'] == employee.id)
        self.assertEqual(row['statuses'][week_start.isoformat()], Attendance.Status.PRESENT)
        self.assertEqual(row['statuses'][(week_start + timedelta(days=1)).isoformat()], Attendance.Status.REMOTE)


class TestHrLeaveRequestsEndpoint(HrEndpointsTestCase):
    def test_get_leave_requests_returns_expected_rows(self):
        employee = baker.make(
            User,
            role=User.Role.SALES,
            department=self.hr_department,
            first_name='Ana',
            last_name='Pop',
            username='ana.pop',
        )
        pending_request = baker.make(
            LeaveRequest,
            employee=employee,
            department=self.hr_department,
            type=LeaveRequest.Type.VACATION,
            from_date='2026-05-04',
            to_date='2026-05-06',
            status=LeaveRequest.Status.PENDING,
        )
        approved_request = baker.make(
            LeaveRequest,
            employee=employee,
            department=self.hr_department,
            type=LeaveRequest.Type.SICK,
            from_date='2026-05-07',
            to_date='2026-05-08',
            status=LeaveRequest.Status.APPROVED,
            approved_by=self.hr_user,
        )

        response = self.hr_client.get('/api/leave-requests/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 2)

        by_id = {item['id']: item for item in response.data}
        self.assertEqual(by_id[pending_request.id]['type'], LeaveRequest.Type.VACATION)
        self.assertEqual(by_id[pending_request.id]['days'], 3)
        self.assertEqual(by_id[approved_request.id]['status'], LeaveRequest.Status.APPROVED)
        self.assertEqual(by_id[approved_request.id]['approved_by']['id'], self.hr_user.id)

    def test_get_leave_requests_status_filter_returns_only_matching_rows(self):
        employee = baker.make(User, role=User.Role.SALES, department=self.hr_department)
        baker.make(
            LeaveRequest,
            employee=employee,
            department=self.hr_department,
            status=LeaveRequest.Status.PENDING,
        )
        baker.make(
            LeaveRequest,
            employee=employee,
            department=self.hr_department,
            status=LeaveRequest.Status.REJECTED,
        )

        response = self.hr_client.get('/api/leave-requests/?status=approved')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_post_leave_requests_creates_pending_status(self):
        employee = baker.make(User, role=User.Role.SALES, department=self.hr_department)

        payload = {
            'employee': employee.id,
            'type': LeaveRequest.Type.VACATION,
            'from_date': '2026-05-01',
            'to_date': '2026-05-03',
            'reason': 'Family event',
        }

        response = self.hr_client.post('/api/leave-requests/', payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        leave_request = LeaveRequest.objects.get(id=response.data['id'])
        self.assertEqual(leave_request.status, LeaveRequest.Status.PENDING)

    def test_patch_leave_request_approve_sets_approved_status(self):
        employee = baker.make(User, role=User.Role.SALES, department=self.hr_department)
        leave_request = baker.make(
            LeaveRequest,
            employee=employee,
            department=self.hr_department,
            status=LeaveRequest.Status.PENDING,
        )

        response = self.hr_client.patch(f'/api/leave-requests/{leave_request.id}/approve/', {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        leave_request.refresh_from_db()
        self.assertEqual(leave_request.status, LeaveRequest.Status.APPROVED)
        self.assertEqual(leave_request.approved_by_id, self.hr_user.id)

    def test_patch_leave_request_reject_sets_rejected_status(self):
        employee = baker.make(User, role=User.Role.SALES, department=self.hr_department)
        leave_request = baker.make(
            LeaveRequest,
            employee=employee,
            department=self.hr_department,
            status=LeaveRequest.Status.PENDING,
        )

        response = self.hr_client.patch(f'/api/leave-requests/{leave_request.id}/reject/', {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        leave_request.refresh_from_db()
        self.assertEqual(leave_request.status, LeaveRequest.Status.REJECTED)
        self.assertEqual(leave_request.approved_by_id, self.hr_user.id)


class TestHrContractsEndpoint(HrEndpointsTestCase):
    def test_get_contracts_returns_all_with_status_computation(self):
        today = timezone.localdate()
        employee = baker.make(User, role=User.Role.SALES, department=self.hr_department)

        active_contract = baker.make(
            Contract,
            contract_number='CTR-100',
            employee=employee,
            department=self.hr_department,
            end_date=today + timedelta(days=90),
        )
        expiring_contract = baker.make(
            Contract,
            contract_number='CTR-101',
            employee=employee,
            department=self.hr_department,
            end_date=today + timedelta(days=10),
        )
        expired_contract = baker.make(
            Contract,
            contract_number='CTR-102',
            employee=employee,
            department=self.hr_department,
            end_date=today - timedelta(days=1),
        )

        response = self.hr_client.get('/api/contracts/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        by_number = {item['contract_number']: item for item in response.data['contracts']}

        self.assertEqual(by_number[active_contract.contract_number]['status'], 'ACTIVE')
        self.assertEqual(by_number[expiring_contract.contract_number]['status'], 'EXPIRING')
        self.assertEqual(by_number[expired_contract.contract_number]['status'], 'EXPIRED')

    def test_get_contracts_expiring_filter_returns_only_expiring(self):
        today = timezone.localdate()
        employee = baker.make(User, role=User.Role.SALES, department=self.hr_department)

        baker.make(
            Contract,
            contract_number='CTR-201',
            employee=employee,
            department=self.hr_department,
            end_date=today + timedelta(days=12),
        )
        baker.make(
            Contract,
            contract_number='CTR-202',
            employee=employee,
            department=self.hr_department,
            end_date=today + timedelta(days=120),
        )

        response = self.hr_client.get('/api/contracts/?status=expiring')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['contracts']), 1)
        self.assertEqual(response.data['contracts'][0]['status'], 'EXPIRING')


class TestHrPayrollEndpoint(HrEndpointsTestCase):
    def test_get_payroll_month_returns_correct_net_calculation(self):
        month_date = timezone.datetime(2026, 4, 1).date()
        employee = baker.make(User, role=User.Role.SALES, department=self.hr_department, first_name='Dana', last_name='Marin')

        baker.make(
            PayrollEntry,
            employee=employee,
            month=month_date,
            gross_salary_ron=Decimal('4000.00'),
            net_salary_ron=Decimal('0.00'),
        )

        response = self.hr_client.get('/api/payroll/?month=2026-04&bonus=500&deductions=200')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        row = response.data['payroll'][0]
        self.assertEqual(Decimal(row['base_salary_ron']), Decimal('4000.00'))
        self.assertEqual(Decimal(row['bonus_ron']), Decimal('500'))
        self.assertEqual(Decimal(row['deductions_ron']), Decimal('200'))
        self.assertEqual(Decimal(row['net_salary_ron']), Decimal('4300.00'))

    def test_payroll_deduction_formula_net_equals_base_plus_bonus_minus_deductions(self):
        month_date = timezone.datetime(2026, 6, 1).date()
        employee = baker.make(User, role=User.Role.IT, department=self.hr_department)

        baker.make(
            PayrollEntry,
            employee=employee,
            month=month_date,
            gross_salary_ron=Decimal('3200.50'),
            net_salary_ron=Decimal('0.00'),
        )

        response = self.hr_client.get('/api/payroll/?month=2026-06&bonus=150.25&deductions=99.75')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        row = response.data['payroll'][0]

        base = Decimal(row['base_salary_ron'])
        bonus = Decimal(row['bonus_ron'])
        deductions = Decimal(row['deductions_ron'])
        net = Decimal(row['net_salary_ron'])

        self.assertEqual(net, base + bonus - deductions)


class TestCeoHrSummaryEndpoint(APITestCase):
    def test_ceo_hr_summary_counts_it_and_sales_departments(self):
        ceo = baker.make(User, role=User.Role.CEO, username='ceo_summary', email='ceo_summary@example.com')
        client = APITestCase.client_class()
        client.force_authenticate(user=ceo)

        it_department = baker.make(Department, name='IT Support', slug='it-support')
        sales_department = baker.make(Department, name='Sales & Marketing', slug='sales-marketing')

        baker.make(User, role=User.Role.IT, department=it_department, is_active=True)
        baker.make(User, role=User.Role.IT, department=it_department, is_active=False)
        baker.make(User, role=User.Role.SALES, department=sales_department, is_active=True)

        response = client.get('/api/hr/ceo-summary/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        by_department = {row['department']: row for row in response.data['department_headcount']}

        self.assertEqual(by_department['IT Support']['total'], 2)
        self.assertEqual(by_department['IT Support']['active'], 1)
        self.assertEqual(by_department['Sales & Marketing']['total'], 1)
        self.assertEqual(by_department['Sales & Marketing']['active'], 1)
