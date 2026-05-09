"""Business tools exposed to the MIEZ Assistant agent."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
from typing import Any

from django.db.models import Count, Sum
from django.utils import timezone

from api.models import Department, LeaveRequest, Order, Report, Ticket, User
from api.report_utils import generate_report_file

from .tools import Tool, agent_tool, get_registry, register_tool


def _permission_error(message: str) -> PermissionError:
    return PermissionError(message)


def _require_roles(user: User, allowed_roles: list[str], message: str) -> None:
    if user.role not in allowed_roles:
        raise _permission_error(message)


def _serialize_department(department: Department | None) -> dict[str, Any] | None:
    if department is None:
        return None
    return {
        'id': department.id,
        'name': department.name,
        'slug': department.slug,
    }


def _serialize_ticket(ticket: Ticket) -> dict[str, Any]:
    return {
        'id': ticket.id,
        'ticket_number': ticket.ticket_number,
        'title': ticket.title,
        'status': 'NEW' if ticket.status == Ticket.Status.OPEN else ticket.status,
        'priority': ticket.priority,
        'requested_by_id': ticket.requested_by_id,
        'requested_by_username': ticket.requested_by.username if ticket.requested_by else None,
        'department': _serialize_department(ticket.department),
    }


def _serialize_employee(employee: User) -> dict[str, Any]:
    return {
        'id': employee.id,
        'username': employee.username,
        'email': employee.email,
        'role': employee.role,
        'department': _serialize_department(employee.department),
        'is_active': employee.is_active,
    }


@agent_tool(name='get_dashboard_summary', description='Get dashboard summary data by module.')
def get_dashboard_summary(module: str, user: User) -> dict[str, Any]:
    module_name = (module or '').strip().lower()
    if module_name == 'sales':
        _require_roles(user, [User.Role.CEO, User.Role.SALES], 'Only CEO and Sales can access the sales dashboard summary.')

        today = timezone.localdate()
        yesterday = today - timedelta(days=1)
        start_of_week = today - timedelta(days=today.weekday())

        base_queryset = Order.objects.all()
        today_stats = base_queryset.filter(date=today).aggregate(
            orders_today=Count('id'),
            revenue_today_ron=Sum('value_ron'),
        )
        yesterday_stats = base_queryset.filter(date=yesterday).aggregate(
            orders_yesterday=Count('id'),
            revenue_yesterday_ron=Sum('value_ron'),
        )

        def pct_change(current_value: Any, previous_value: Any) -> float:
            current_numeric = float(current_value or 0)
            previous_numeric = float(previous_value or 0)
            if previous_numeric == 0:
                return 100.0 if current_numeric > 0 else 0.0
            return round(((current_numeric - previous_numeric) / previous_numeric) * 100, 2)

        orders_today = today_stats['orders_today'] or 0
        revenue_today_ron = Decimal(str(today_stats['revenue_today_ron'] or 0)).quantize(Decimal('0.01'))
        orders_yesterday = yesterday_stats['orders_yesterday'] or 0
        revenue_yesterday_ron = yesterday_stats['revenue_yesterday_ron'] or 0

        return {
            'orders_today': orders_today,
            'revenue_today_ron': f'{revenue_today_ron:.2f}',
            'pending_orders': base_queryset.filter(status=Order.Status.PENDING).count(),
            'returns_this_week': base_queryset.filter(
                status=Order.Status.RETURNED,
                date__gte=start_of_week,
                date__lte=today,
            ).count(),
            'pct_changes': {
                'orders': pct_change(orders_today, orders_yesterday),
                'revenue': pct_change(revenue_today_ron, revenue_yesterday_ron),
            },
        }

    if module_name == 'hr':
        _require_roles(user, [User.Role.CEO, User.Role.HR], 'Only CEO and HR can access the HR dashboard summary.')

        today = timezone.localdate()
        month_start = today.replace(day=1)
        employees = User.objects.all()
        total_employees = employees.count()
        active_employees = employees.filter(is_active=True).count()
        full_time_employees = employees.filter(full_time=True).count()

        return {
            'total_employees': total_employees,
            'new_hires_this_month': employees.filter(start_date__gte=month_start, start_date__lte=today).count(),
            'leave_requests_this_month': LeaveRequest.objects.filter(
                created_at__date__gte=month_start,
                created_at__date__lte=today,
            ).count(),
            'pending_leave_requests': LeaveRequest.objects.filter(status=LeaveRequest.Status.PENDING).count(),
            'full_time_employees': full_time_employees,
            'non_full_time_employees': max(total_employees - full_time_employees, 0),
            'retention_rate': round((active_employees / total_employees) * 100, 1) if total_employees else 0.0,
            'active_employees': active_employees,
        }

    raise ValueError(f'Unsupported module: {module}')


@agent_tool(name='query_tickets', description='Query tickets by status.')
def query_tickets(status: str, user: User) -> list[dict[str, Any]]:
    _require_roles(user, [User.Role.CEO, User.Role.IT], 'Only CEO and IT can query tickets.')

    status_name = (status or '').strip().upper()
    status_map = {
        'NEW': Ticket.Status.OPEN,
        'OPEN': Ticket.Status.OPEN,
        'IN_PROGRESS': Ticket.Status.IN_PROGRESS,
        'RESOLVED': Ticket.Status.RESOLVED,
        'CLOSED': Ticket.Status.CLOSED,
    }
    if status_name not in status_map:
        raise ValueError(f'Unsupported ticket status: {status}')

    resolved_status = status_map[status_name]
    tickets = Ticket.objects.select_related('department', 'requested_by').filter(status=resolved_status).order_by('id')
    return [_serialize_ticket(ticket) for ticket in tickets]


@agent_tool(name='query_employees', description='Query employees.')
def query_employees(user: User) -> list[dict[str, Any]]:
    _require_roles(user, [User.Role.CEO, User.Role.HR], 'Only CEO and HR can query employees.')

    employees = User.objects.select_related('department').all().order_by('id')
    return [_serialize_employee(employee) for employee in employees]


@agent_tool(name='create_ticket', description='Create a support ticket.')
def create_ticket(user: User, **payload: Any) -> Ticket:
    return Ticket.objects.create(
        title=payload['title'],
        description=payload.get('description', ''),
        category=payload.get('category', ''),
        priority=payload.get('priority', Ticket.Priority.MEDIUM),
        department_id=payload.get('department_id'),
        requested_for_id=payload.get('requested_for_id'),
        assigned_to_id=payload.get('assigned_to_id'),
        location=payload.get('location', ''),
        requested_by=user,
        status=Ticket.Status.OPEN,
    )


@agent_tool(name='create_leave_request', description='Create a leave request.')
def create_leave_request(user: User, **payload: Any) -> LeaveRequest:
    _require_roles(user, [User.Role.HR], 'Only HR can create leave requests through the assistant.')

    employee = payload['employee']
    if isinstance(employee, int):
        employee = User.objects.select_related('department').get(id=employee)

    return LeaveRequest.objects.create(
        employee=employee,
        department=employee.department,
        type=payload.get('type', LeaveRequest.Type.VACATION),
        from_date=payload['from_date'],
        to_date=payload['to_date'],
        reason=payload.get('reason', ''),
        status=LeaveRequest.Status.PENDING,
    )


@agent_tool(name='generate_report', description='Generate a report from an existing report definition.')
def generate_report(user: User, slug: str) -> Report:
    if user.role != User.Role.CEO and not user.is_staff:
        raise _permission_error('Only CEO or staff users can generate reports through the assistant.')

    report = Report.objects.get(slug=slug)
    generate_report_file(report, user=user)
    return report


def register_default_tools() -> None:
    registry = get_registry()
    if registry.get('get_dashboard_summary') is not None:
        return

    register_tool(Tool.from_callable(get_dashboard_summary))
    register_tool(Tool.from_callable(query_tickets, required_permission='manage_tickets'))
    register_tool(Tool.from_callable(query_employees, required_permission='manage_employees'))
    register_tool(Tool.from_callable(create_ticket))
    register_tool(Tool.from_callable(create_leave_request, required_permission='process_leave_requests'))
    register_tool(Tool.from_callable(generate_report, required_permission='view_financial_reports'))