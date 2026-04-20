from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone
from model_bakery import baker
from rest_framework.test import APIClient

from api.models import Attendance, Contract, Department, LeaveRequest, PayrollEntry, User


pytestmark = pytest.mark.django_db


@pytest.fixture
def hr_user():
    return baker.make(
        User,
        role=User.Role.HR,
        username='hr_test_user',
        email='hr_test_user@example.com',
    )


@pytest.fixture
def hr_client(hr_user):
    client = APIClient()
    client.force_authenticate(user=hr_user)
    return client


@pytest.fixture
def hr_department():
    return baker.make(Department, name='Human Resources', slug='hr')


def test_get_employees_returns_full_list_with_expected_fields(hr_client, hr_department):
    baker.make(
        User,
        role=User.Role.SALES,
        department=hr_department,
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
        department=hr_department,
        first_name='Mihai',
        last_name='Ionescu',
        username='mihai.ionescu',
        email='mihai.ionescu@example.com',
        employment_type=User.EmploymentType.CONTRACTOR,
        full_time=False,
        is_active=False,
    )

    response = hr_client.get('/api/employees/?page_size=100')

    assert response.status_code == 200
    assert response.data['count'] >= 2
    assert len(response.data['results']) >= 2

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
    assert expected_keys.issubset(first.keys())


def test_get_attendance_week_returns_expected_grid(hr_client, hr_department):
    today = timezone.localdate()
    week_start = today - timedelta(days=today.weekday())

    employee = baker.make(
        User,
        role=User.Role.SALES,
        department=hr_department,
        first_name='Elena',
        last_name='Vasilescu',
        username='elena.v',
    )

    baker.make(Attendance, employee=employee, date=week_start, status=Attendance.Status.PRESENT)
    baker.make(Attendance, employee=employee, date=week_start + timedelta(days=1), status=Attendance.Status.REMOTE)

    response = hr_client.get(f'/api/attendance/?week={week_start.isoformat()}')

    assert response.status_code == 200
    assert response.data['week_start'] == week_start.isoformat()
    assert len(response.data['days']) == 7

    row = next(item for item in response.data['grid'] if item['employee_id'] == employee.id)
    assert row['statuses'][week_start.isoformat()] == Attendance.Status.PRESENT
    assert row['statuses'][(week_start + timedelta(days=1)).isoformat()] == Attendance.Status.REMOTE


def test_post_leave_requests_creates_pending_status(hr_client, hr_department):
    employee = baker.make(User, role=User.Role.SALES, department=hr_department)

    payload = {
        'employee': employee.id,
        'type': LeaveRequest.Type.VACATION,
        'from_date': '2026-05-01',
        'to_date': '2026-05-03',
        'reason': 'Family event',
    }

    response = hr_client.post('/api/leave-requests/', payload, format='json')

    assert response.status_code == 201
    leave_request = LeaveRequest.objects.get(id=response.data['id'])
    assert leave_request.status == LeaveRequest.Status.PENDING


def test_patch_leave_request_approve_sets_approved_status(hr_client, hr_user, hr_department):
    employee = baker.make(User, role=User.Role.SALES, department=hr_department)
    leave_request = baker.make(
        LeaveRequest,
        employee=employee,
        department=hr_department,
        status=LeaveRequest.Status.PENDING,
    )

    response = hr_client.patch(f'/api/leave-requests/{leave_request.id}/approve/', {}, format='json')

    assert response.status_code == 200
    leave_request.refresh_from_db()
    assert leave_request.status == LeaveRequest.Status.APPROVED
    assert leave_request.approved_by_id == hr_user.id


def test_patch_leave_request_reject_sets_rejected_status(hr_client, hr_user, hr_department):
    employee = baker.make(User, role=User.Role.SALES, department=hr_department)
    leave_request = baker.make(
        LeaveRequest,
        employee=employee,
        department=hr_department,
        status=LeaveRequest.Status.PENDING,
    )

    response = hr_client.patch(f'/api/leave-requests/{leave_request.id}/reject/', {}, format='json')

    assert response.status_code == 200
    leave_request.refresh_from_db()
    assert leave_request.status == LeaveRequest.Status.REJECTED
    assert leave_request.approved_by_id == hr_user.id


def test_get_contracts_returns_all_with_status_computation(hr_client, hr_department):
    today = timezone.localdate()
    employee = baker.make(User, role=User.Role.SALES, department=hr_department)

    active_contract = baker.make(
        Contract,
        contract_number='CTR-100',
        employee=employee,
        department=hr_department,
        end_date=today + timedelta(days=90),
    )
    expiring_contract = baker.make(
        Contract,
        contract_number='CTR-101',
        employee=employee,
        department=hr_department,
        end_date=today + timedelta(days=10),
    )
    expired_contract = baker.make(
        Contract,
        contract_number='CTR-102',
        employee=employee,
        department=hr_department,
        end_date=today - timedelta(days=1),
    )

    response = hr_client.get('/api/contracts/')

    assert response.status_code == 200
    by_number = {item['contract_number']: item for item in response.data['contracts']}

    assert by_number[active_contract.contract_number]['status'] == 'ACTIVE'
    assert by_number[expiring_contract.contract_number]['status'] == 'EXPIRING'
    assert by_number[expired_contract.contract_number]['status'] == 'EXPIRED'


def test_get_contracts_expiring_filter_returns_only_expiring(hr_client, hr_department):
    today = timezone.localdate()
    employee = baker.make(User, role=User.Role.SALES, department=hr_department)

    baker.make(
        Contract,
        contract_number='CTR-201',
        employee=employee,
        department=hr_department,
        end_date=today + timedelta(days=12),
    )
    baker.make(
        Contract,
        contract_number='CTR-202',
        employee=employee,
        department=hr_department,
        end_date=today + timedelta(days=120),
    )

    response = hr_client.get('/api/contracts/?status=expiring')

    assert response.status_code == 200
    assert len(response.data['contracts']) == 1
    assert response.data['contracts'][0]['status'] == 'EXPIRING'


def test_get_payroll_month_returns_correct_net_calculation(hr_client, hr_department):
    month_date = timezone.datetime(2026, 4, 1).date()
    employee = baker.make(User, role=User.Role.SALES, department=hr_department, first_name='Dana', last_name='Marin')

    baker.make(
        PayrollEntry,
        employee=employee,
        month=month_date,
        gross_salary_ron=Decimal('4000.00'),
        net_salary_ron=Decimal('0.00'),
    )

    response = hr_client.get('/api/payroll/?month=2026-04&bonus=500&deductions=200')

    assert response.status_code == 200
    row = response.data['payroll'][0]
    assert Decimal(row['base_salary_ron']) == Decimal('4000.00')
    assert Decimal(row['bonus_ron']) == Decimal('500')
    assert Decimal(row['deductions_ron']) == Decimal('200')
    assert Decimal(row['net_salary_ron']) == Decimal('4300.00')


def test_payroll_deduction_formula_net_equals_base_plus_bonus_minus_deductions(hr_client, hr_department):
    month_date = timezone.datetime(2026, 6, 1).date()
    employee = baker.make(User, role=User.Role.IT, department=hr_department)

    baker.make(
        PayrollEntry,
        employee=employee,
        month=month_date,
        gross_salary_ron=Decimal('3200.50'),
        net_salary_ron=Decimal('0.00'),
    )

    response = hr_client.get('/api/payroll/?month=2026-06&bonus=150.25&deductions=99.75')

    assert response.status_code == 200
    row = response.data['payroll'][0]

    base = Decimal(row['base_salary_ron'])
    bonus = Decimal(row['bonus_ron'])
    deductions = Decimal(row['deductions_ron'])
    net = Decimal(row['net_salary_ron'])

    assert net == base + bonus - deductions
