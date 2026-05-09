"""
Management command to generate weekly HR digest for CEO.
Analyzes HR metrics and creates structured insights with notifications.
"""

import json
from datetime import timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Q, Count, F, ExpressionWrapper, DecimalField
from django.db.models.functions import TruncWeek

from api.models import (
    User, Department, Report, Notification, LeaveRequest, 
    Attendance, PayrollEntry, Contract
)


class DigestGenerator:
    """Generates HR digest with insights and metrics."""
    
    def __init__(self):
        self.insights = {
            'critical': [],
            'warning': [],
            'info': [],
        }
        self.generated_at = timezone.now()
        self.week_start = self._get_week_start()
        self.week_end = self.week_start + timedelta(days=6)
        
    def _get_week_start(self):
        """Get the start of the current week (Monday)."""
        today = timezone.localdate()
        return today - timedelta(days=today.weekday())
    
    def generate(self):
        """Generate all insights and return structured digest."""
        self._check_pending_leave_requests()
        self._check_low_attendance_rates()
        self._check_payroll_issues()
        self._check_excessive_leave()
        self._check_contract_expiring()
        self._check_inactive_employees()
        
        # Generate period string (e.g., "Week of 2026-05-05")
        period = f"Week of {self.week_start.strftime('%Y-%m-%d')}"
        
        # Create summary line based on critical insights
        summary_line = self._create_summary_line()
        
        digest = {
            'week': self.week_start.isoformat(),
            'generated_at': self.generated_at.isoformat(),
            'critical': self.insights['critical'],
            'warning': self.insights['warning'],
            'info': self.insights['info'],
            'summary_line': summary_line,
            'period': period,
        }
        
        return digest
    
    def _create_summary_line(self):
        """Create a concise summary line based on critical insights."""
        critical_count = len(self.insights['critical'])
        warning_count = len(self.insights['warning'])
        
        if critical_count == 0 and warning_count == 0:
            return 'All HR metrics within normal range'
        
        parts = []
        if critical_count > 0:
            parts.append(f'{critical_count} critical HR issue{"s" if critical_count != 1 else ""} require{"s" if critical_count == 1 else ""} your attention')
        if warning_count > 0:
            parts.append(f'{warning_count} warning{"s" if warning_count != 1 else ""}')
        
        return ' and '.join(parts)
    
    def _add_insight(self, level, title, description, suggested_action, related_employee=None, related_department=None):
        """Add an insight to the digest."""
        insight = {
            'title': title,
            'description': description,
            'suggested_action': suggested_action,
            'related_employee': related_employee,
            'related_department': related_department,
        }
        self.insights[level].append(insight)
    
    def _check_pending_leave_requests(self):
        """Check for pending leave requests awaiting approval."""
        pending = LeaveRequest.objects.filter(
            status=LeaveRequest.Status.PENDING,
            created_at__gte=timezone.now() - timedelta(days=7)
        ).select_related('employee', 'department').count()
        
        if pending > 0:
            self._add_insight(
                level='warning',
                title=f'{pending} Pending Leave Request{"s" if pending != 1 else ""}',
                description=f'{pending} leave request{"s" if pending != 1 else ""} {"is" if pending == 1 else "are"} awaiting approval for the current period.',
                suggested_action='Review and approve/reject pending leave requests in the HR portal.',
                related_department='Human Resources'
            )
    
    def _check_low_attendance_rates(self):
        """Check if attendance rate drops below 80% in any department."""
        today = timezone.localdate()
        week_attendance = (
            Attendance.objects
            .filter(
                date__gte=self.week_start,
                date__lte=today,
                status__in=[Attendance.Status.PRESENT, Attendance.Status.REMOTE]
            )
            .values('employee__department__name')
            .annotate(
                total=Count('id'),
                attended=Count('id', filter=Q(status__in=[Attendance.Status.PRESENT, Attendance.Status.REMOTE]))
            )
        )
        
        for row in week_attendance:
            dept_name = row['employee__department__name'] or 'Unassigned'
            total = row['total'] or 0
            attended = row['attended'] or 0
            
            if total > 0:
                rate = (attended / total) * 100
                if rate < 80:
                    self._add_insight(
                        level='warning',
                        title=f'Low Attendance in {dept_name}',
                        description=f'Attendance rate in {dept_name} is {rate:.1f}% this week (target: 80%+).',
                        suggested_action='Investigate and follow up with department managers about absences.',
                        related_department=dept_name
                    )
    
    def _check_excessive_leave(self):
        """Check if any department has more than 25% of staff on leave."""
        today = timezone.localdate()
        departments = Department.objects.all()
        
        for department in departments:
            total_employees = User.objects.filter(
                department=department,
                is_active=True
            ).count()
            
            if total_employees == 0:
                continue
            
            on_leave = LeaveRequest.objects.filter(
                department=department,
                status=LeaveRequest.Status.APPROVED,
                from_date__lte=today,
                to_date__gte=today
            ).count()
            
            leave_percentage = (on_leave / total_employees) * 100
            
            if leave_percentage > 25:
                self._add_insight(
                    level='warning',
                    title=f'High Leave Usage in {department.name}',
                    description=f'{leave_percentage:.1f}% of {department.name} staff is on approved leave today.',
                    suggested_action='Ensure adequate coverage; consider adjusting project timelines if necessary.',
                    related_department=department.name
                )
    
    def _check_payroll_issues(self):
        """Check for unpaid payroll entries."""
        current_month = timezone.now().date().replace(day=1)
        unpaid = PayrollEntry.objects.filter(
            month__gte=current_month - timedelta(days=30),
            paid=False
        ).select_related('employee').count()
        
        if unpaid > 0:
            self._add_insight(
                level='critical',
                title=f'{unpaid} Unpaid Payroll Entr{"ies" if unpaid != 1 else "y"}',
                description=f'{unpaid} payroll entr{"ies" if unpaid != 1 else "y"} remain unpaid for the current/recent pay period.',
                suggested_action='Process outstanding payroll payments immediately to avoid legal/compliance issues.',
                related_department='Finance & Payroll'
            )
    
    def _check_contract_expiring(self):
        """Check for contracts expiring within 30 days."""
        today = timezone.localdate()
        expiring = Contract.objects.filter(
            end_date__gte=today,
            end_date__lte=today + timedelta(days=30)
        ).select_related('employee', 'department').count()
        
        if expiring > 0:
            self._add_insight(
                level='warning',
                title=f'{expiring} Contract{"s" if expiring != 1 else ""} Expiring Soon',
                description=f'{expiring} employee contract{"s" if expiring != 1 else ""} {"expire" if expiring != 1 else "expires"} within the next 30 days.',
                suggested_action='Review contracts and decide on renewals or transitions.',
                related_department='Human Resources'
            )
    
    def _check_inactive_employees(self):
        """Check for inactive employees who may need attention."""
        inactive = User.objects.filter(
            is_active=False,
            last_login__isnull=False
        ).exclude(
            role=User.Role.CEO
        ).count()
        
        if inactive > 5:
            self._add_insight(
                level='info',
                title=f'{inactive} Inactive Employees in System',
                description=f'{inactive} employees are marked as inactive but still in the system.',
                suggested_action='Review inactive employee records and archive if no longer relevant.',
                related_department='Human Resources'
            )
    
    def _check_employee_turnover(self):
        """Check for recent employee departures."""
        thirty_days_ago = timezone.now() - timedelta(days=30)
        
        # Check users deactivated in the last 30 days
        recent_inactive = User.objects.filter(
            is_active=False,
            date_joined__lt=thirty_days_ago
        ).exclude(
            role=User.Role.CEO
        ).count()
        
        if recent_inactive > 0:
            self._add_insight(
                level='info',
                title='Recent Employee Status Changes',
                description=f'{recent_inactive} employee{"s" if recent_inactive != 1 else ""} recently marked as inactive.',
                suggested_action='Review employee records for any necessary HR follow-ups.',
                related_department='Human Resources'
            )


class Command(BaseCommand):
    """Django management command to generate HR digest."""
    
    help = 'Generate weekly HR digest for CEO with insights and metrics'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--save-report',
            action='store_true',
            help='Save the digest as a Report record in the database',
        )
        parser.add_argument(
            '--notify-hr',
            action='store_true',
            help='Send notification to HR Manager if critical issues exist',
        )
    
    def handle(self, *args, **options):
        # Generate the digest
        generator = DigestGenerator()
        digest = generator.generate()
        
        # Output the digest as JSON
        self.stdout.write(self.style.SUCCESS('\n=== Weekly HR Digest ===\n'))
        self.stdout.write(json.dumps(digest, indent=2, default=str))
        
        # Save as Report if requested
        if options['save_report']:
            self._save_report(digest, generator)
        
        # Create notification if requested and critical issues exist
        if options['notify_hr'] and digest['critical']:
            self._notify_hr_manager(digest)
        
        # Log if no anomalies detected
        if not digest['critical'] and not digest['warning'] and not digest['info']:
            self.stdout.write(
                self.style.WARNING('\nNo anomalies detected - no notification sent.\n')
            )
    
    def _save_report(self, digest, generator):
        """Save the digest as a Report record."""
        try:
            report = Report.objects.create(
                name=f'HR Weekly Digest - {generator.week_start.strftime("%Y-%m-%d")}',
                slug=f'hr-digest-{generator.week_start.strftime("%Y%m%d")}',
                category=Report.Category.HR,
                period=digest['period'],
                file_path='',  # JSON stored in database, not as file
                file_size_kb=0,
                generated_by=self._get_ceo_user(),
                generated_at=generator.generated_at,
            )
            
            # Store full digest as the report content (could be extended to save to file)
            report.digest_data = digest  # Note: requires adding to model or custom field
            
            self.stdout.write(
                self.style.SUCCESS(f'\n✓ Report saved: {report.name}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'\n✗ Failed to save report: {str(e)}')
            )
    
    def _notify_hr_manager(self, digest):
        """Create notification for HR Manager if critical issues exist."""
        try:
            hr_managers = User.objects.filter(
                role=User.Role.HR,
                is_active=True
            )
            
            if not hr_managers.exists():
                self.stdout.write(
                    self.style.WARNING('\nNo active HR Manager found for notification.')
                )
                return
            
            critical_count = len(digest['critical'])
            summary = digest['summary_line']
            
            for hr_manager in hr_managers:
                Notification.objects.create(
                    recipient=hr_manager,
                    title='🚨 Critical HR Issues Detected',
                    body=summary,
                    link='/reports?category=HR',
                )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✓ Notifications sent to {hr_managers.count()} HR Manager(s)'
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'\n✗ Failed to send notifications: {str(e)}')
            )
    
    def _get_ceo_user(self):
        """Get the first active CEO user, or None."""
        return User.objects.filter(
            role=User.Role.CEO,
            is_active=True
        ).first()
