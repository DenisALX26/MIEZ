"""Weekly HR digest — DB-driven, no AI. Swap with run_hr_agent in CRONJOBS to switch modes."""

from __future__ import annotations

import datetime
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count, Q, Sum
from django.utils import timezone

from api.models import (
    Attendance, Contract, LeaveRequest, Notification,
    PayrollEntry, Report, User, Workflow, WorkflowLog,
)

WORKFLOW_NAME = 'HR Insights Agent'
SERVICE_USERNAME = 'hr-agent'


def _week_bounds(week_override: str | None) -> tuple[datetime.date, datetime.date]:
    if week_override:
        year_str, week_str = week_override.split('-W')
        monday = datetime.date.fromisocalendar(int(year_str), int(week_str), 1)
    else:
        today = timezone.localdate()
        monday = today - timedelta(days=today.weekday() + 7)
    return monday, monday + timedelta(days=6)


def _month_bounds(d: datetime.date) -> tuple[datetime.date, datetime.date]:
    start = d.replace(day=1)
    end = (start.replace(day=28) + timedelta(days=4)).replace(day=1)
    return start, end


def _fmt(d: datetime.date | None) -> str:
    return d.strftime('%b %-d') if d else '—'


def _fmt_long(d: datetime.date | None) -> str:
    return d.strftime('%b %-d, %Y') if d else '—'


def build_report(week_start: datetime.date, week_end: datetime.date) -> str:
    iso_year, iso_week, _ = week_start.isocalendar()
    iso_label = f'{iso_year}-W{iso_week:02d}'

    # Leave
    leave_qs = LeaveRequest.objects.select_related('employee', 'department').filter(
        from_date__lte=week_end, to_date__gte=week_start
    )
    pending = list(leave_qs.filter(status=LeaveRequest.Status.PENDING))
    approved = leave_qs.filter(status=LeaveRequest.Status.APPROVED).count()
    rejected = leave_qs.filter(status=LeaveRequest.Status.REJECTED).count()

    # Attendance
    att_rows = list(
        Attendance.objects
        .filter(date__gte=week_start, date__lte=week_end)
        .values('employee__department__name')
        .annotate(
            total=Count('id'),
            present=Count('id', filter=Q(status__in=[
                Attendance.Status.PRESENT, Attendance.Status.REMOTE,
            ])),
        )
        .order_by('employee__department__name')
    )
    low_att = [r for r in att_rows if r['total'] and (r['present'] / r['total']) * 100 < 80]

    # Contracts expiring within 30 days
    today = timezone.localdate()
    expiring = list(
        Contract.objects
        .select_related('employee', 'department')
        .exclude(end_date__isnull=True)
        .filter(end_date__gte=today, end_date__lte=today + timedelta(days=30))
        .order_by('end_date')
    )

    # Payroll
    month_start, month_end = _month_bounds(week_start)
    agg = PayrollEntry.objects.filter(month__gte=month_start, month__lt=month_end).aggregate(
        total=Count('id'),
        gross=Sum('gross_salary_ron'),
        net=Sum('net_salary_ron'),
        unpaid=Count('id', filter=Q(paid=False)),
    )
    p_total  = agg['total']  or 0
    p_gross  = Decimal(str(agg['gross'] or 0)).quantize(Decimal('0.01'))
    p_net    = Decimal(str(agg['net']   or 0)).quantize(Decimal('0.01'))
    p_unpaid = agg['unpaid'] or 0

    # Critical
    critical: list[str] = []
    if p_unpaid:
        critical.append(f'**Unpaid Payroll** — {p_unpaid} entr{"ies" if p_unpaid != 1 else "y"} unpaid for {month_start.strftime("%B %Y")}.')
    if not att_rows and not p_total:
        critical.append('**Data Completeness Issue** — No attendance or payroll data. Verify data pipeline status.')
    for r in low_att:
        rate = round((r['present'] / r['total']) * 100, 1)
        critical.append(f'**Low Attendance: {r["employee__department__name"]}** — {rate}% this week (target 80%+).')

    L: list[str] = []

    # Header
    L += [
        f'## **WEEKLY HR DIGEST - WEEK {iso_label}**',
        f'### **{_fmt(week_start)}-{_fmt_long(week_end)}**',
        '', '---', '',
    ]

    # Executive summary
    L.append('### **EXECUTIVE SUMMARY**')
    parts: list[str] = []
    if pending:    parts.append(f'{len(pending)} leave request{"s" if len(pending) != 1 else ""} pending approval.')
    if expiring:   parts.append(f'{len(expiring)} contract{"s" if len(expiring) != 1 else ""} expiring within 30 days.')
    if low_att:    parts.append(f'{len(low_att)} department{"s" if len(low_att) != 1 else ""} below 80% attendance.')
    if p_unpaid:   parts.append(f'{p_unpaid} unpaid payroll {"entries" if p_unpaid != 1 else "entry"}.')
    if not parts:  parts.append('No critical HR issues this week.')
    L.append(' '.join(parts))
    L += ['', '---', '']

    # Leave
    L += [
        '### **LEAVE REQUESTS SUMMARY**',
        '**Overall Status:**',
        f'- **Pending:** {len(pending)} request{"s" if len(pending) != 1 else ""}',
        f'- **Approved:** {approved} request{"s" if approved != 1 else ""}',
        f'- **Rejected:** {rejected} request{"s" if rejected != 1 else ""}',
        '',
    ]
    if pending:
        L += [
            '**Pending Request Details:**',
            '| Employee | Department | Type | Dates | Reason |',
            '|----------|-----------|------|-------|--------|',
        ]
        for lr in pending:
            emp    = lr.employee.username if lr.employee else '—'
            dept   = lr.department.name if lr.department else '—'
            dates  = f'{_fmt(lr.from_date)} – {_fmt(lr.to_date)}'
            reason = (lr.reason or '—')[:60]
            L.append(f'| {emp} | {dept} | {lr.type} | {dates} | {reason} |')
        L += ['', '**Action Required:** Review and approve/reject pending leave requests.']
    else:
        L.append('**Status:** No pending leave requests this week.')
    L += ['', '---', '']

    # Attendance
    L.append('### **ATTENDANCE HIGHLIGHTS**')
    if not att_rows:
        L += [
            '**Status:** No attendance data available for this week.',
            '- Consider verifying data collection systems are operational.',
        ]
    elif low_att:
        L.append('**Departments below 80% attendance:**')
        for r in low_att:
            rate = round((r['present'] / r['total']) * 100, 1)
            L.append(f'- **{r["employee__department__name"]}**: {rate}% ({r["present"]}/{r["total"]} records)')
    else:
        L.append('**Status:** All departments above 80% attendance threshold.')
    L += ['', '---', '']

    # Contracts
    L.append('### **CONTRACTS REQUIRING ACTION**')
    if not expiring:
        L += [
            '**Status:** No contracts expiring within the next 30 days.',
            '- All active employment contracts are current.',
        ]
    else:
        L += [
            f'**{len(expiring)} contract{"s" if len(expiring) != 1 else ""} expiring within 30 days:**',
            '| Employee | Department | Type | End Date |',
            '|----------|-----------|------|----------|',
        ]
        for c in expiring:
            emp  = c.employee.username if c.employee else '—'
            dept = c.department.name if c.department else '—'
            L.append(f'| {emp} | {dept} | {c.type} | {c.end_date} |')
    L += ['', '---', '']

    # Payroll
    L += [
        '### **PAYROLL STATUS**',
        f'**Month:** {month_start.strftime("%B %Y")}',
        f'- **Total Entries:** {p_total}',
        f'- **Gross Payroll:** RON {p_gross}',
        f'- **Net Payroll:** RON {p_net}',
        f'- **Unpaid Entries:** {p_unpaid}',
        '',
    ]
    if p_unpaid:
        L.append(f'**Action Required:** {p_unpaid} payroll {"entries" if p_unpaid != 1 else "entry"} pending payment.')
    elif not p_total:
        L.append('**Status:** No payroll data recorded for this month.')
    else:
        L.append('**Status:** All payroll entries have been paid.')
    L += ['', '---', '']

    # Critical
    L.append('### **CRITICAL ISSUES REQUIRING IMMEDIATE ATTENTION**')
    if critical:
        L.append('\n⚠️ **HIGH PRIORITY:**')
        for i, issue in enumerate(critical, 1):
            L.append(f'{i}. {issue}')
    else:
        L.append('No critical issues this week.')

    L += ['', '---', '', f'**Report Generated:** Automated Weekly HR Analysis for {iso_label}']

    return '\n'.join(L)


class Command(BaseCommand):
    help = 'Generate weekly HR digest from DB (no AI). Swap with run_hr_agent in CRONJOBS to use AI instead.'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Print without saving.')
        parser.add_argument('--week', type=str, default=None, help='ISO week e.g. 2026-W19. Defaults to last week.')

    def handle(self, *args, **options):
        dry_run: bool = options['dry_run']
        week_arg: str | None = options['week']

        workflow, _ = Workflow.objects.get_or_create(
            name=WORKFLOW_NAME,
            defaults={
                'trigger_type': 'WEEKLY_AT_TIME',
                'trigger_config': {'day_of_week': 'monday', 'time': '06:00'},
                'is_active': True,
            },
        )
        if not workflow.is_active:
            self.stdout.write(self.style.WARNING(f'Workflow "{WORKFLOW_NAME}" is disabled. Skipping.'))
            return

        week_start, week_end = _week_bounds(week_arg)
        iso_year, iso_week, _ = week_start.isocalendar()
        iso_label = f'{iso_year}-W{iso_week:02d}'
        self.stdout.write(f'Generating HR digest for {iso_label} ({week_start} → {week_end})')

        log = WorkflowLog(workflow=workflow, trigger_input={'week': iso_label, 'dry_run': dry_run})

        try:
            content = build_report(week_start, week_end)
            self.stdout.write('\n' + content + '\n')

            if not dry_run:
                service_user, _ = User.objects.get_or_create(
                    username=SERVICE_USERNAME,
                    defaults={'email': 'hr-agent@miez.internal', 'role': User.Role.HR},
                )
                slug = f'hr-digest-{week_start.strftime("%Y%m%d")}'
                report, created = Report.objects.get_or_create(
                    slug=slug,
                    defaults={
                        'name': f'HR Weekly Digest — {iso_label}',
                        'category': Report.Category.HR,
                        'period': f'Week of {week_start.isoformat()}',
                        'file_path': '',
                        'file_size_kb': 0,
                        'generated_by': service_user,
                        'generated_at': timezone.now(),
                        'digest_data': {
                            'week': iso_label,
                            'week_start': week_start.isoformat(),
                            'week_end': week_end.isoformat(),
                            'content': content,
                        },
                    },
                )
                if not created:
                    report.digest_data = {
                        'week': iso_label,
                        'week_start': week_start.isoformat(),
                        'week_end': week_end.isoformat(),
                        'content': content,
                    }
                    report.generated_at = timezone.now()
                    report.save(update_fields=['digest_data', 'generated_at'])
                self.stdout.write(self.style.SUCCESS(f'Report saved: {report.name} (id={report.id})'))

            log.trigger_result = {'status': 'success', 'week': iso_label}
            log.save()

        except Exception as exc:
            log.error_message = str(exc)
            log.trigger_result = {'status': 'error'}
            log.save()
            hr_managers = User.objects.filter(role=User.Role.HR, is_active=True).exclude(username=SERVICE_USERNAME)
            for manager in hr_managers:
                Notification.objects.create(
                    recipient=manager,
                    title='HR Digest Error',
                    body=f'Weekly HR digest failed: {str(exc)[:200]}',
                    link='/reports?category=HR',
                )
            raise CommandError(str(exc)) from exc
