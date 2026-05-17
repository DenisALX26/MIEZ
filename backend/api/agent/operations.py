"""Business tools exposed to the MIEZ Assistant agent."""

from __future__ import annotations

import datetime
from collections import defaultdict
from datetime import timedelta
from decimal import Decimal
from typing import Any

from django.db.models import Avg, Count, DurationField, ExpressionWrapper, F, Q, Sum
from django.db.models.functions import TruncWeek
from django.utils import timezone

from api.models import Attendance, Contract, Department, Invoice, LeaveRequest, Order, PayrollEntry, Product, Report, StockMovement, Ticket, User
from api.report_utils import generate_report_file

from .tools import Tool, agent_tool, get_registry, register_tool


def _parse_iso_week(week: str) -> tuple[datetime.date, datetime.date]:
    """Parse ISO week string '2026-W18' to (monday, sunday)."""
    year_str, week_str = week.split('-W')
    monday = datetime.date.fromisocalendar(int(year_str), int(week_str), 1)
    return monday, monday + timedelta(days=6)


def _permission_error(message: str) -> PermissionError:
    return PermissionError(message)


def _require_roles(user: User, allowed_roles: list[str], message: str) -> None:
    if user.role not in allowed_roles:
        raise _permission_error(message)


def can_generate_reports(user: User) -> bool:
    if user.role == User.Role.CEO:
        return True

    position = (user.position or '').strip().lower()
    if not position:
        return False

    return any(token in position for token in ('manager', 'lead', 'head', 'director'))


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


def _serialize_order(order: Order) -> dict[str, Any]:
    return {
        'id': order.id,
        'order_number': order.order_number,
        'status': order.status,
        'channel': order.channel,
        'customer_id': order.customer_id,
        'customer_name': order.customer.name if order.customer else None,
        'value_ron': f'{Decimal(str(order.value_ron or 0)).quantize(Decimal("0.01")):.2f}',
        'date': order.date.isoformat() if order.date else None,
    }


def _serialize_inventory(product: Product) -> dict[str, Any]:
    return {
        'id': product.id,
        'name': product.name,
        'sku': product.sku,
        'category': product.category,
        'stock_count': product.stock_count,
        'min_stock': product.min_stock,
        'status': product.availability,
    }


def _normalized_limit(limit: int | None, default_limit: int = 10) -> int:
    if limit is None:
        return default_limit
    return max(1, min(int(limit), 10))


@agent_tool(
    name='get_dashboard_summary',
    description='Get KPI summary for a business module. module must be one of: sales, hr, it, inventory.',
    schema={
        'type': 'object',
        'properties': {
            'module': {'type': 'string', 'enum': ['sales', 'hr', 'it', 'inventory']},
        },
        'required': ['module'],
    },
)
def get_dashboard_summary(module: str, user: User) -> dict[str, Any]:
    module_name = (module or '').strip().lower()

    def _result(kpis: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            'module': module_name,
            'kpis': kpis,
            'generated_at': timezone.now().isoformat(),
        }

    if module_name == 'sales':
        _require_roles(user, [User.Role.CEO, User.Role.SALES], 'Only CEO and Sales can access the sales dashboard summary.')

        today = timezone.localdate()
        yesterday = today - timedelta(days=1)
        start_of_week = today - timedelta(days=today.weekday())
        base_qs = Order.objects.all()

        today_stats = base_qs.filter(date=today).aggregate(
            orders_today=Count('id'),
            revenue_today_ron=Sum('value_ron'),
        )
        yesterday_stats = base_qs.filter(date=yesterday).aggregate(
            orders_yesterday=Count('id'),
            revenue_yesterday_ron=Sum('value_ron'),
        )

        def _pct(current: Any, previous: Any) -> float:
            c, p = float(current or 0), float(previous or 0)
            if p == 0:
                return 100.0 if c > 0 else 0.0
            return round(((c - p) / p) * 100, 2)

        orders_today = today_stats['orders_today'] or 0
        revenue_today = Decimal(str(today_stats['revenue_today_ron'] or 0)).quantize(Decimal('0.01'))
        orders_yesterday = yesterday_stats['orders_yesterday'] or 0
        revenue_yesterday = yesterday_stats['revenue_yesterday_ron'] or 0

        return _result([
            {'label': 'Orders Today', 'value': orders_today},
            {'label': 'Revenue Today (RON)', 'value': f'{revenue_today:.2f}'},
            {'label': 'Pending Orders', 'value': base_qs.filter(status=Order.Status.PENDING).count()},
            {'label': 'Returns This Week', 'value': base_qs.filter(status=Order.Status.RETURNED, date__gte=start_of_week, date__lte=today).count()},
            {'label': 'Orders Change vs Yesterday (%)', 'value': _pct(orders_today, orders_yesterday)},
            {'label': 'Revenue Change vs Yesterday (%)', 'value': _pct(revenue_today, revenue_yesterday)},
        ])

    if module_name == 'hr':
        _require_roles(user, [User.Role.CEO, User.Role.HR], 'Only CEO and HR can access the HR dashboard summary.')

        today = timezone.localdate()
        month_start = today.replace(day=1)
        employees = User.objects.all()
        total = employees.count()
        active = employees.filter(is_active=True).count()
        full_time = employees.filter(full_time=True).count()

        return _result([
            {'label': 'Total Employees', 'value': total},
            {'label': 'Active Employees', 'value': active},
            {'label': 'New Hires This Month', 'value': employees.filter(start_date__gte=month_start, start_date__lte=today).count()},
            {'label': 'Pending Leave Requests', 'value': LeaveRequest.objects.filter(status=LeaveRequest.Status.PENDING).count()},
            {'label': 'Full-Time Employees', 'value': full_time},
            {'label': 'Retention Rate (%)', 'value': round((active / total) * 100, 1) if total else 0.0},
        ])

    if module_name == 'it':
        _require_roles(user, [User.Role.CEO, User.Role.IT], 'Only CEO and IT can access the IT dashboard summary.')

        now = timezone.now()
        week_start = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)

        stats = Ticket.objects.aggregate(
            open_tickets=Count('id', filter=Q(status=Ticket.Status.OPEN)),
            in_progress=Count('id', filter=Q(status=Ticket.Status.IN_PROGRESS)),
            resolved_this_week=Count('id', filter=Q(status=Ticket.Status.RESOLVED, resolved_at__gte=week_start)),
            critical_open=Count('id', filter=Q(status=Ticket.Status.OPEN, priority__in=[Ticket.Priority.HIGH, Ticket.Priority.URGENT])),
        )

        resolved_qs = Ticket.objects.filter(status=Ticket.Status.RESOLVED, resolved_at__gte=week_start).annotate(
            duration=ExpressionWrapper(F('resolved_at') - F('created_at'), output_field=DurationField())
        )
        perf = resolved_qs.aggregate(avg_res_time=Avg('duration'), sla_met=Count('id', filter=Q(duration__lte=timedelta(hours=4))))

        avg_hrs = round(perf['avg_res_time'].total_seconds() / 3600, 2) if perf['avg_res_time'] else 0.0
        total_resolved = stats['resolved_this_week'] or 0
        sla_pct = round((perf['sla_met'] / total_resolved) * 100, 2) if total_resolved else 0.0

        return _result([
            {'label': 'Open Tickets', 'value': stats['open_tickets']},
            {'label': 'In Progress', 'value': stats['in_progress']},
            {'label': 'Resolved This Week', 'value': total_resolved},
            {'label': 'Critical Open', 'value': stats['critical_open']},
            {'label': 'Avg Resolution Time (hrs)', 'value': avg_hrs},
            {'label': 'SLA Met (%)', 'value': sla_pct},
        ])

    if module_name == 'inventory':
        _require_roles(user, [User.Role.CEO, User.Role.INVENTORY], 'Only CEO and Inventory can access the inventory dashboard summary.')

        import datetime as _dt
        today = _dt.date.today()

        return _result([
            {'label': 'Total Products', 'value': Product.objects.count()},
            {'label': 'Low Stock', 'value': Product.objects.filter(stock_count__lt=F('min_stock'), stock_count__gt=0).count()},
            {'label': 'Out of Stock', 'value': Product.objects.filter(stock_count=0).count()},
            {'label': 'Deliveries Today', 'value': StockMovement.objects.filter(movement_type=StockMovement.Type.INBOUND, expected_date=today).count()},
        ])

    raise ValueError(f'Unsupported module: {module}. Must be one of: sales, hr, it, inventory.')


@agent_tool(name='query_tickets', description='Query tickets by status.')
def query_tickets(
    user: User,
    status: str | None = None,
    priority: str | None = None,
    assigned_to: int | str | None = None,
    limit: int = 10,
) -> list[dict[str, Any]]:
    _require_roles(user, [User.Role.CEO, User.Role.IT], 'Only CEO and IT can query tickets.')

    queryset = Ticket.objects.select_related('department', 'requested_by', 'assigned_to').all()

    status_name = (status or '').strip().upper()
    status_map = {
        'NEW': Ticket.Status.OPEN,
        'OPEN': Ticket.Status.OPEN,
        'IN_PROGRESS': Ticket.Status.IN_PROGRESS,
        'RESOLVED': Ticket.Status.RESOLVED,
        'CLOSED': Ticket.Status.CLOSED,
    }
    if status_name and status_name not in status_map:
        raise ValueError(f'Unsupported ticket status: {status}')
    if status_name:
        queryset = queryset.filter(status=status_map[status_name])

    if priority:
        priority_name = priority.strip().upper()
        valid_priorities = {choice[0] for choice in Ticket.Priority.choices}
        if priority_name not in valid_priorities:
            raise ValueError(f'Unsupported ticket priority: {priority}')
        queryset = queryset.filter(priority=priority_name)

    if assigned_to is not None:
        if isinstance(assigned_to, int) or (isinstance(assigned_to, str) and assigned_to.isdigit()):
            queryset = queryset.filter(assigned_to_id=int(assigned_to))
        elif isinstance(assigned_to, str):
            queryset = queryset.filter(assigned_to__username=assigned_to)
        else:
            raise ValueError('assigned_to must be a user id or username')

    tickets = queryset.order_by('-created_at')[:_normalized_limit(limit)]
    return [_serialize_ticket(ticket) for ticket in tickets]


@agent_tool(name='query_employees', description='Query employees.')
def query_employees(
    user: User,
    department: int | str | None = None,
    role: str | None = None,
    is_active: bool | None = None,
    limit: int = 10,
) -> list[dict[str, Any]]:
    _require_roles(user, [User.Role.CEO, User.Role.HR], 'Only CEO and HR can query employees.')

    employees = User.objects.select_related('department').all()

    if department is not None:
        if isinstance(department, int) or (isinstance(department, str) and department.isdigit()):
            employees = employees.filter(department_id=int(department))
        elif isinstance(department, str):
            employees = employees.filter(Q(department__slug=department) | Q(department__name__iexact=department))
        else:
            raise ValueError('department must be an id, slug, or name')

    if role:
        role_name = role.strip().upper()
        valid_roles = {choice[0] for choice in User.Role.choices}
        if role_name not in valid_roles:
            raise ValueError(f'Unsupported employee role: {role}')
        employees = employees.filter(role=role_name)

    if is_active is not None:
        employees = employees.filter(is_active=bool(is_active))

    employees = employees.order_by('id')[:_normalized_limit(limit)]
    return [_serialize_employee(employee) for employee in employees]


@agent_tool(name='query_orders', description='Query orders by status, channel, and customer.')
def query_orders(
    user: User,
    status: str | None = None,
    channel: str | None = None,
    customer: str | None = None,
    limit: int = 10,
) -> list[dict[str, Any]]:
    _require_roles(user, [User.Role.CEO, User.Role.SALES], 'Only CEO and Sales can query orders.')

    queryset = Order.objects.select_related('customer').all()

    if status:
        status_name = status.strip().upper()
        valid_statuses = {choice[0] for choice in Order.Status.choices}
        if status_name not in valid_statuses:
            raise ValueError(f'Unsupported order status: {status}')
        queryset = queryset.filter(status=status_name)

    if channel:
        channel_name = channel.strip().upper()
        valid_channels = {choice[0] for choice in Order.Channel.choices}
        if channel_name not in valid_channels:
            raise ValueError(f'Unsupported order channel: {channel}')
        queryset = queryset.filter(channel=channel_name)

    if customer:
        queryset = queryset.filter(customer__name__icontains=customer)

    orders = queryset.order_by('-date', '-id')[:_normalized_limit(limit)]
    return [_serialize_order(order) for order in orders]


@agent_tool(name='query_inventory', description='Query inventory by status, category, and stock thresholds.')
def query_inventory(
    user: User,
    status: str | None = None,
    category: str | None = None,
    below_min_stock: bool | None = None,
    limit: int = 10,
) -> list[dict[str, Any]]:
    _require_roles(user, [User.Role.CEO, User.Role.INVENTORY], 'Only CEO and Inventory can query inventory.')

    queryset = Product.objects.all()

    if category:
        category_input = category.strip()
        valid_categories = {choice[0] for choice in Product.Category.choices}
        matched = next((c for c in valid_categories if c.lower() == category_input.lower()), None)
        if matched is None:
            raise ValueError(f'Unsupported product category: {category}')
        queryset = queryset.filter(category=matched)

    if below_min_stock is True:
        queryset = queryset.filter(stock_count__lt=F('min_stock'))

    products = queryset.order_by('id')

    if status:
        status_name = status.strip().lower()
        status_map = {
            'out_of_stock': 'out of stock',
            'low_stock': 'low stock',
            'in_stock': 'in stock',
        }
        normalized_status = status_map.get(status_name, status_name)
        products = [product for product in products if product.availability.lower() == normalized_status]
        return [_serialize_inventory(product) for product in products[:_normalized_limit(limit)]]

    return [_serialize_inventory(product) for product in products[:_normalized_limit(limit)]]


@agent_tool(
    name='create_ticket',
    description='Create a support ticket. Available to all roles.',
    schema={
        'type': 'object',
        'properties': {
            'title': {'type': 'string', 'description': 'Short ticket title'},
            'description': {'type': 'string', 'description': 'Detailed description of the issue'},
            'category': {'type': 'string', 'description': 'Ticket category (e.g. Hardware, Software, Network)'},
            'priority': {'type': 'string', 'enum': ['LOW', 'MEDIUM', 'HIGH', 'URGENT']},
            'location': {'type': 'string', 'description': 'Physical location of the issue'},
        },
        'required': ['title'],
    },
)
def create_ticket(
    user: User,
    title: str,
    description: str = '',
    category: str = '',
    priority: str = Ticket.Priority.MEDIUM,
    location: str = '',
) -> dict[str, Any]:
    ticket = Ticket.objects.create(
        title=title,
        description=description,
        category=category,
        priority=priority,
        location=location,
        requested_by=user,
        status=Ticket.Status.OPEN,
    )
    return {'ticket_number': ticket.ticket_number, 'status': ticket.status}


@agent_tool(
    name='create_leave_request',
    description='Create a leave request. Not available to CEO.',
    schema={
        'type': 'object',
        'properties': {
            'employee': {'type': 'integer', 'description': 'Employee ID (HR only; defaults to the requesting user)'},
            'type': {'type': 'string', 'enum': ['VACATION', 'SICK', 'UNPAID']},
            'from_date': {'type': 'string', 'description': 'Start date (YYYY-MM-DD)'},
            'to_date': {'type': 'string', 'description': 'End date (YYYY-MM-DD)'},
            'reason': {'type': 'string', 'description': 'Reason for the leave'},
        },
        'required': ['from_date', 'to_date'],
    },
)
def create_leave_request(
    user: User,
    from_date: Any,
    to_date: Any,
    employee: Any = None,
    type: str = LeaveRequest.Type.VACATION,
    reason: str = '',
) -> dict[str, Any]:
    if user.role == User.Role.CEO:
        raise _permission_error('CEO cannot create leave requests through the assistant.')

    if employee is None:
        target_employee = user
    elif isinstance(employee, int):
        target_employee = User.objects.select_related('department').get(id=employee)
    else:
        target_employee = employee

    lr = LeaveRequest.objects.create(
        employee=target_employee,
        department=target_employee.department,
        type=type,
        from_date=from_date,
        to_date=to_date,
        reason=reason,
        status=LeaveRequest.Status.PENDING,
    )
    return {'id': lr.id, 'status': lr.status}


@agent_tool(name='generate_report', description='Generate a report from an existing report definition.')
def generate_report(user: User, slug: str) -> Report:
    if not can_generate_reports(user):
        raise _permission_error('Only the CEO or department managers can generate reports through the assistant.')

    report = Report.objects.get(slug=slug)
    generate_report_file(report, user=user)
    return report


@agent_tool(name='query_leave_requests', description='Query leave requests, optionally filtered by ISO week (e.g. 2026-W18), status, or department.')
def query_leave_requests(
    user: User,
    week: str | None = None,
    status: str | None = None,
    department: int | str | None = None,
    limit: int = 10,
) -> list[dict[str, Any]]:
    _require_roles(user, [User.Role.CEO, User.Role.HR], 'Only CEO and HR can query leave requests.')

    queryset = LeaveRequest.objects.select_related('employee', 'department').all()

    if week:
        week_start, week_end = _parse_iso_week(week)
        queryset = queryset.filter(from_date__lte=week_end, to_date__gte=week_start)

    if status:
        status_name = status.strip().upper()
        valid_statuses = {choice[0] for choice in LeaveRequest.Status.choices}
        if status_name not in valid_statuses:
            raise ValueError(f'Unsupported leave request status: {status}')
        queryset = queryset.filter(status=status_name)

    if department is not None:
        if isinstance(department, int) or (isinstance(department, str) and department.isdigit()):
            queryset = queryset.filter(department_id=int(department))
        elif isinstance(department, str):
            queryset = queryset.filter(Q(department__slug=department) | Q(department__name__iexact=department))

    leave_requests = queryset.order_by('-created_at')[:_normalized_limit(limit)]
    return [
        {
            'id': lr.id,
            'employee_id': lr.employee_id,
            'employee_username': lr.employee.username if lr.employee else None,
            'department': _serialize_department(lr.department),
            'type': lr.type,
            'from_date': lr.from_date.isoformat() if lr.from_date else None,
            'to_date': lr.to_date.isoformat() if lr.to_date else None,
            'status': lr.status,
            'reason': lr.reason,
        }
        for lr in leave_requests
    ]


@agent_tool(name='query_attendance', description='Get attendance summary by department for an ISO week (e.g. 2026-W18). Defaults to the current week.')
def query_attendance(
    user: User,
    week: str | None = None,
    department: int | str | None = None,
) -> list[dict[str, Any]]:
    _require_roles(user, [User.Role.CEO, User.Role.HR], 'Only CEO and HR can query attendance.')

    if week:
        week_start, week_end = _parse_iso_week(week)
    else:
        today = timezone.localdate()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)

    queryset = Attendance.objects.filter(date__gte=week_start, date__lte=week_end)

    if department is not None:
        if isinstance(department, int) or (isinstance(department, str) and department.isdigit()):
            queryset = queryset.filter(employee__department_id=int(department))
        elif isinstance(department, str):
            queryset = queryset.filter(
                Q(employee__department__slug=department) | Q(employee__department__name__iexact=department)
            )

    rows = (
        queryset
        .values('employee__department__name')
        .annotate(
            total=Count('id'),
            present=Count('id', filter=Q(status__in=[Attendance.Status.PRESENT, Attendance.Status.REMOTE])),
        )
        .order_by('employee__department__name')
    )

    return [
        {
            'department': row['employee__department__name'] or 'Unassigned',
            'total_records': row['total'],
            'present_or_remote': row['present'],
            'attendance_rate_pct': round((row['present'] / row['total']) * 100, 1) if row['total'] else 0.0,
            'week': week_start.isoformat(),
        }
        for row in rows
    ]


@agent_tool(
    name='get_attendance_trend',
    description='Get attendance trend by department for the last N weeks (default 4). Flags low department attendance and repeated unexcused absences.',
    schema={
        'type': 'object',
        'properties': {
            'weeks': {'type': 'integer', 'minimum': 1, 'maximum': 12, 'default': 4},
        },
    },
)
def get_attendance_trend(
    user: User,
    weeks: int = 4,
) -> list[dict[str, Any]]:
    _require_roles(user, [User.Role.CEO, User.Role.HR], 'Only CEO and HR can access attendance trends.')

    total_weeks = max(1, min(int(weeks), 12))
    today = timezone.localdate()
    current_week_start = today - timedelta(days=today.weekday())
    first_week_start = current_week_start - timedelta(weeks=total_weeks - 1)
    last_week_end = current_week_start + timedelta(days=6)
    repeated_absence_window_start = current_week_start - timedelta(weeks=3)

    base_queryset = Attendance.objects.filter(date__gte=first_week_start, date__lte=last_week_end)

    weekly_department_rows = (
        base_queryset
        .annotate(week=TruncWeek('date'))
        .values('week', 'employee__department__name')
        .annotate(
            total=Count('id'),
            attended=Count('id', filter=Q(status__in=[Attendance.Status.PRESENT, Attendance.Status.REMOTE])),
            approved_leave=Count('id', filter=Q(status=Attendance.Status.LEAVE)),
            unexcused_absence=Count('id', filter=Q(status=Attendance.Status.ABSENT)),
        )
        .order_by('week', 'employee__department__name')
    )

    repeated_absence_rows = (
        Attendance.objects.filter(
            date__gte=repeated_absence_window_start,
            date__lte=last_week_end,
        )
        .filter(status=Attendance.Status.ABSENT)
        .values('employee_id')
        .annotate(total_unexcused_absences=Count('id'))
    )
    repeated_absence_map = {
        row['employee_id']: row['total_unexcused_absences']
        for row in repeated_absence_rows
        if (row['total_unexcused_absences'] or 0) >= 3
    }

    absent_employee_rows = (
        base_queryset
        .filter(status__in=[Attendance.Status.ABSENT, Attendance.Status.LEAVE])
        .annotate(week=TruncWeek('date'))
        .values(
            'week',
            'employee__department__name',
            'employee_id',
            'employee__first_name',
            'employee__last_name',
            'employee__username',
            'status',
        )
        .annotate(count=Count('id'))
        .order_by('week', 'employee__department__name', 'employee_id', 'status')
    )

    employees_absent_by_bucket: dict[tuple[datetime.date, str], list[dict[str, Any]]] = defaultdict(list)
    for row in absent_employee_rows:
        week_value = row['week']
        week_date = week_value.date() if hasattr(week_value, 'date') else week_value
        department_name = row['employee__department__name'] or 'Unassigned'

        full_name = f"{row['employee__first_name']} {row['employee__last_name']}".strip() or row['employee__username']
        is_unexcused = row['status'] == Attendance.Status.ABSENT
        employee_id = row['employee_id']

        employees_absent_by_bucket[(week_date, department_name)].append(
            {
                'name': full_name,
                'count': row['count'] or 0,
                'absence_type': 'unexcused' if is_unexcused else 'approved_leave',
                'flag_repeated_absence': bool(is_unexcused and repeated_absence_map.get(employee_id, 0) >= 3),
            }
        )

    results: list[dict[str, Any]] = []
    for row in weekly_department_rows:
        week_value = row['week']
        week_date = week_value.date() if hasattr(week_value, 'date') else week_value
        department_name = row['employee__department__name'] or 'Unassigned'

        total_records = row['total'] or 0
        attended_records = row['attended'] or 0
        attendance_pct = round((attended_records / total_records) * 100, 1) if total_records else 0.0

        results.append(
            {
                'week': week_date.isoformat(),
                'department': department_name,
                'attendance_pct': attendance_pct,
                'employees_absent': employees_absent_by_bucket.get((week_date, department_name), []),
                'flag_low_attendance': attendance_pct < 85.0,
                'approved_leave_count': row['approved_leave'] or 0,
                'unexcused_absence_count': row['unexcused_absence'] or 0,
            }
        )

    return results


@agent_tool(
    name='get_leave_patterns',
    description='Get leave pattern observations for the last N weeks (default 8). Returns observations only, not conclusions.',
    schema={
        'type': 'object',
        'properties': {
            'weeks': {'type': 'integer', 'minimum': 1, 'maximum': 12, 'default': 8},
        },
    },
)
def get_leave_patterns(
    user: User,
    weeks: int = 8,
) -> list[dict[str, Any]]:
    _require_roles(user, [User.Role.CEO, User.Role.HR], 'Only CEO and HR can access leave patterns.')

    total_weeks = max(1, min(int(weeks), 12))
    today = timezone.localdate()
    window_start = today - timedelta(weeks=total_weeks)

    queryset = LeaveRequest.objects.select_related('employee', 'employee__department', 'department').filter(
        created_at__date__gte=window_start,
        created_at__date__lte=today,
    )

    observations: list[dict[str, Any]] = []

    monday_friday_counts: dict[int, dict[str, Any]] = defaultdict(lambda: {'employee_name': '', 'occurrences': 0})
    for request in queryset.order_by('employee_id', 'created_at', 'id'):
        request_date = request.created_at.date()
        if request_date.weekday() not in (0, 4):
            continue

        employee_name = f'{request.employee.first_name} {request.employee.last_name}'.strip() or request.employee.username
        bucket = monday_friday_counts[request.employee_id]
        bucket['employee_name'] = employee_name
        bucket['occurrences'] += 1

    for bucket in monday_friday_counts.values():
        if bucket['occurrences'] >= 3:
            observations.append(
                {
                    'pattern_type': 'monday_friday_leave_requests',
                    'employee_name': bucket['employee_name'],
                    'description': (
                        f"Observation: {bucket['employee_name']} submitted leave requests starting on Monday or Friday "
                        f"{bucket['occurrences']} times in the last {total_weeks} weeks."
                    ),
                    'occurrences': bucket['occurrences'],
                }
            )

    medical_rows = list(
        queryset.filter(type=LeaveRequest.Type.SICK)
        .values('department_id', 'department__name', 'created_at')
        .order_by('department_id', 'created_at', 'id')
    )
    medical_by_department: dict[str, list[datetime.date]] = defaultdict(list)
    for row in medical_rows:
        department_name = row['department__name'] or 'Unassigned'
        created_at = row['created_at']
        request_date = created_at.date() if hasattr(created_at, 'date') else created_at
        medical_by_department[department_name].append(request_date)

    for department_name, request_dates in medical_by_department.items():
        if len(request_dates) < 3:
            continue

        best_start_index = 0
        best_end_index = 0
        left = 0
        for right, right_date in enumerate(request_dates):
            while request_dates[left] < right_date - timedelta(days=13):
                left += 1
            if right - left > best_end_index - best_start_index:
                best_start_index = left
                best_end_index = right

        occurrences = best_end_index - best_start_index + 1
        if occurrences > 2:
            window_start_date = request_dates[best_start_index]
            window_end_date = request_dates[best_end_index]
            observations.append(
                {
                    'pattern_type': 'medical_leave_cluster',
                    'department': department_name,
                    'description': (
                        f"Observation: {department_name} logged {occurrences} medical leave requests between "
                        f"{window_start_date.isoformat()} and {window_end_date.isoformat()}."
                    ),
                    'occurrences': occurrences,
                }
            )

    for employee_id, employee_requests in _group_leave_requests_by_employee(queryset).items():
        previous_rejected = False
        consecutive_after_rejection = 0
        employee_name = employee_requests[0]['employee_name'] if employee_requests else ''

        for request in employee_requests:
            if previous_rejected:
                consecutive_after_rejection += 1
                observations.append(
                    {
                        'pattern_type': 'leave_after_rejection',
                        'employee_name': employee_name,
                        'description': (
                            f"Observation: {employee_name} submitted a new leave request after a rejected request on "
                            f"{request['created_at'].date().isoformat()}."
                        ),
                        'occurrences': consecutive_after_rejection,
                    }
                )
            previous_rejected = request['status'] == LeaveRequest.Status.REJECTED

    observations.sort(key=lambda item: (item['pattern_type'], item.get('employee_name') or item.get('department') or ''))
    return observations


def _group_leave_requests_by_employee(queryset) -> dict[int, list[dict[str, Any]]]:
    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    rows = (
        queryset
        .values(
            'employee_id',
            'employee__first_name',
            'employee__last_name',
            'employee__username',
            'status',
            'created_at',
            'id',
        )
        .order_by('employee_id', 'created_at', 'id')
    )

    for row in rows:
        employee_name = f"{row['employee__first_name']} {row['employee__last_name']}".strip() or row['employee__username']
        grouped[row['employee_id']].append(
            {
                'employee_name': employee_name,
                'status': row['status'],
                'created_at': row['created_at'],
            }
        )

    return grouped


@agent_tool(name='query_contracts', description='Query employee contracts expiring within a number of days (default 30).')
def query_contracts(
    user: User,
    expiring_within_days: int | None = None,
    limit: int = 10,
) -> list[dict[str, Any]]:
    _require_roles(user, [User.Role.CEO, User.Role.HR], 'Only CEO and HR can query contracts.')

    queryset = Contract.objects.select_related('employee', 'department').exclude(end_date__isnull=True)
    today = timezone.localdate()
    days = int(expiring_within_days) if expiring_within_days is not None else 30
    queryset = queryset.filter(end_date__gte=today, end_date__lte=today + timedelta(days=days))

    contracts = queryset.order_by('end_date')[:_normalized_limit(limit)]
    return [
        {
            'id': c.id,
            'contract_number': c.contract_number,
            'employee_id': c.employee_id,
            'employee_username': c.employee.username if c.employee else None,
            'department': _serialize_department(c.department),
            'type': c.type,
            'end_date': c.end_date.isoformat() if c.end_date else None,
            'salary_ron': f'{Decimal(str(c.salary_ron or 0)).quantize(Decimal("0.01")):.2f}',
        }
        for c in contracts
    ]


@agent_tool(name='query_payroll', description='Get payroll summary for a month (format: YYYY-MM, defaults to current month).')
def query_payroll(
    user: User,
    month: str | None = None,
) -> dict[str, Any]:
    _require_roles(user, [User.Role.CEO, User.Role.HR], 'Only CEO and HR can query payroll.')

    if month:
        year_str, month_str = month.split('-')
        month_date = datetime.date(int(year_str), int(month_str), 1)
    else:
        today = timezone.localdate()
        month_date = today.replace(day=1)

    next_month = (month_date.replace(day=28) + timedelta(days=4)).replace(day=1)
    entries = PayrollEntry.objects.filter(month__gte=month_date, month__lt=next_month)

    agg = entries.aggregate(
        total_entries=Count('id'),
        total_gross=Sum('gross_salary_ron'),
        total_net=Sum('net_salary_ron'),
        unpaid_count=Count('id', filter=Q(paid=False)),
    )

    return {
        'month': month_date.strftime('%Y-%m'),
        'total_entries': agg['total_entries'] or 0,
        'total_gross_ron': f'{Decimal(str(agg["total_gross"] or 0)).quantize(Decimal("0.01")):.2f}',
        'total_net_ron': f'{Decimal(str(agg["total_net"] or 0)).quantize(Decimal("0.01")):.2f}',
        'unpaid_count': agg['unpaid_count'] or 0,
    }


def register_default_tools() -> None:
    registry = get_registry()
    if registry.get('get_dashboard_summary') is not None:
        return

    register_tool(Tool.from_callable(get_dashboard_summary))
    register_tool(Tool.from_callable(query_orders, required_permission='view_sales_reports'))
    register_tool(Tool.from_callable(query_tickets, required_permission='manage_tickets'))
    register_tool(Tool.from_callable(query_employees, required_permission='manage_employees'))
    register_tool(Tool.from_callable(query_inventory, required_permission='manage_stock'))
    register_tool(Tool.from_callable(create_ticket))
    register_tool(Tool.from_callable(create_leave_request, required_permission='process_leave_requests'))
    register_tool(Tool.from_callable(generate_report, required_permission='view_financial_reports'))
    register_tool(Tool.from_callable(query_leave_requests, required_permission='view_hr_dashboard'))
    register_tool(Tool.from_callable(query_attendance, required_permission='view_hr_dashboard'))
    register_tool(Tool.from_callable(get_leave_patterns, required_permission='view_hr_dashboard'))
    register_tool(Tool.from_callable(get_attendance_trend, required_permission='view_hr_dashboard'))
    register_tool(Tool.from_callable(query_contracts, required_permission='manage_employees'))
    register_tool(Tool.from_callable(query_payroll, required_permission='view_payroll'))