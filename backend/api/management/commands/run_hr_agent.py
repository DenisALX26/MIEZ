"""
Management command to run the HR Insights Agent.

Checks Workflow.is_active, runs AgentRunner as the hr-agent service user,
stores the digest in Report(category=HR), logs to WorkflowLog, and
notifies HR managers on error.
"""

from __future__ import annotations

import datetime
import json
import logging
from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from api.models import Notification, Report, User, Workflow, WorkflowLog
from api.agent.operations import register_default_tools
from api.agent.runner import AgentRunner
from api.agent.tools import get_registry

logger = logging.getLogger(__name__)

WORKFLOW_NAME = 'HR Insights Agent'
SERVICE_USERNAME = 'hr-agent'


def _get_week_bounds(week_override: str | None) -> tuple[datetime.date, datetime.date]:
    if week_override:
        year_str, week_str = week_override.split('-W')
        monday = datetime.date.fromisocalendar(int(year_str), int(week_str), 1)
    else:
        today = timezone.localdate()
        # previous week
        monday = today - timedelta(days=today.weekday() + 7)
    return monday, monday + timedelta(days=6)


def _build_agent_prompt(week_start: datetime.date, week_end: datetime.date) -> str:
    iso_week = f'{week_start.isocalendar()[0]}-W{week_start.isocalendar()[1]:02d}'
    return (
        f'You are running an automated weekly HR analysis for the week {iso_week} '
        f'({week_start.isoformat()} to {week_end.isoformat()}).\n\n'
        'Please perform the following analysis using the available tools:\n'
        '1. Query leave requests for this week and summarize by status (pending/approved/rejected).\n'
        '2. Get attendance rates by department for this week and flag any department below 80%.\n'
        '3. Check contracts expiring within the next 60 days and list them. Escalation severity rule: if an employee has an expiring contract AND holds a key role AND has open dependencies (has_open_tickets or has_pending_leave), flag as CRITICAL. If purely expiring with no open dependencies, flag as WARNING.\n'
        '4. Get payroll summary for the current month and report any unpaid entries.\n\n'
        'Produce a structured weekly HR digest with:\n'
        '- Executive summary (2-3 sentences)\n'
        '- Leave requests summary\n'
        '- Attendance highlights\n'
        '- Contracts requiring action\n'
        '- Payroll status\n'
        '- Any critical issues requiring immediate attention\n\n'
        'Be concise and actionable. Format the response in clear sections.'
    )


class Command(BaseCommand):
    help = 'Run the HR Insights Agent to generate a weekly HR digest.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run the agent but do not save the report or send notifications.',
        )
        parser.add_argument(
            '--week',
            type=str,
            default=None,
            help='ISO week to analyse (e.g. 2026-W18). Defaults to the previous week.',
        )

    def handle(self, *args, **options):
        dry_run: bool = options['dry_run']
        week_arg: str | None = options['week']

        # 1. Check Workflow toggle
        try:
            workflow = Workflow.objects.get(name=WORKFLOW_NAME)
        except Workflow.DoesNotExist:
            self.stdout.write(self.style.WARNING(
                f'Workflow "{WORKFLOW_NAME}" not found — creating it as active.'
            ))
            workflow = Workflow.objects.create(
                name=WORKFLOW_NAME,
                trigger_type='WEEKLY_AT_TIME',
                trigger_config={'day_of_week': 'monday', 'time': '06:00', 'managed_by': 'run_hr_agent'},
                is_active=True,
            )

        if not workflow.is_active:
            self.stdout.write(self.style.WARNING(
                f'Workflow "{WORKFLOW_NAME}" is disabled. Skipping.'
            ))
            return

        # 2. Get (or atomically create) the service user. get_or_create handles the
        # race where concurrent runs (cron + threaded RunInsightsAgentView triggers)
        # would otherwise both try to INSERT the same username and hit a
        # UniqueViolation.
        service_user, created = User.objects.get_or_create(
            username=SERVICE_USERNAME,
            defaults={
                'email': 'hr-agent@miez.internal',
                'role': User.Role.HR,
                'is_active': True,
            },
        )
        if created:
            service_user.set_unusable_password()
            service_user.save(update_fields=['password'])
            self.stdout.write(self.style.WARNING(
                f'Service user "{SERVICE_USERNAME}" not found — created it.'
            ))

        # 3. Determine week bounds
        week_start, week_end = _get_week_bounds(week_arg)
        iso_week = f'{week_start.isocalendar()[0]}-W{week_start.isocalendar()[1]:02d}'
        self.stdout.write(f'Running HR agent for week {iso_week} ({week_start} → {week_end})')

        # 4. Set up tools and runner
        register_default_tools()
        all_tools = get_registry().get_all()

        runner = AgentRunner(user=service_user, tools=all_tools)
        prompt = _build_agent_prompt(week_start, week_end)

        # 5. Run the agent
        log_entry = WorkflowLog(
            workflow=workflow,
            trigger_type='WEEKLY_AT_TIME',
        )

        try:
            result = runner.run(prompt)
            response_value = result.get('response')
            if not isinstance(response_value, str):
                raise CommandError(
                    f'Agent returned a non-text response ({type(response_value).__name__}); aborting digest.'
                )
            digest_text: str = response_value
            tool_calls = result.get('tool_calls_made', [])

            self.stdout.write(self.style.SUCCESS('\n=== HR Agent Digest ===\n'))
            self.stdout.write(digest_text)

            slug = f'hr-agent-{week_start.strftime("%Y%m%d")}'

            if not dry_run:
                # 6. Save Report
                report_name = f'HR Agent Digest — {iso_week}'

                report, created = Report.objects.get_or_create(
                    slug=slug,
                    defaults={
                        'name': report_name,
                        'category': Report.Category.HR,
                        'period': f'Week of {week_start.isoformat()}',
                        'file_path': '',
                        'file_size_kb': 0,
                        'generated_by': service_user,
                        'generated_at': timezone.now(),
                        'digest_data': {
                            'week': iso_week,
                            'week_start': week_start.isoformat(),
                            'week_end': week_end.isoformat(),
                            'content': digest_text,
                            'tool_calls': len(tool_calls),
                        },
                    },
                )
                if not created:
                    report.digest_data = {
                        'week': iso_week,
                        'week_start': week_start.isoformat(),
                        'week_end': week_end.isoformat(),
                        'content': digest_text,
                        'tool_calls': len(tool_calls),
                    }
                    report.generated_at = timezone.now()
                    report.save(update_fields=['digest_data', 'generated_at'])

                self.stdout.write(self.style.SUCCESS(f'\nReport saved: {report_name} (id={report.id})'))
                self._notify_hr_managers_digest(report_id=report.id, digest_text=digest_text)

            log_entry.actions_log = [{
                'action': 'GENERATE_REPORT',
                'success': True,
                'message': f'Report slug: {slug if not dry_run else "dry-run"}, tool_calls: {len(tool_calls)}',
            }]
            log_entry.success = True
            log_entry.save()

        except Exception as exc:
            error_msg = str(exc)
            logger.exception('HR agent failed: %s', error_msg)
            log_entry.actions_log = [{'action': 'GENERATE_REPORT', 'success': False, 'message': error_msg}]
            log_entry.success = False
            log_entry.save()

            if not dry_run:
                self._notify_hr_managers(error_msg)

            raise CommandError(f'HR agent failed: {error_msg}') from exc

    def _notify_hr_managers(self, error_msg: str) -> None:
        hr_managers = User.objects.filter(role=User.Role.HR, is_active=True).exclude(username=SERVICE_USERNAME)
        for manager in hr_managers:
            Notification.objects.create(
                recipient=manager,
                title='HR Agent Error',
                body=f'The weekly HR agent failed: {error_msg[:200]}',
                link='/reports?category=HR',
            )
        if hr_managers.exists():
            self.stdout.write(self.style.WARNING(
                f'Error notifications sent to {hr_managers.count()} HR manager(s).'
            ))

    @staticmethod
    def _extract_digest_summary(digest_text: str) -> str:
        if not digest_text:
            return 'Weekly HR digest generated.'

        summary = ''
        try:
            payload = json.loads(digest_text)
            if isinstance(payload, dict):
                summary = (
                    str(payload.get('summary_line') or '').strip()
                    or str(payload.get('executive_summary') or '').strip()
                )
        except Exception:
            summary = ''

        if summary:
            return summary[:300]

        single_line = ' '.join(digest_text.split())
        return single_line[:300] if single_line else 'Weekly HR digest generated.'

    def _notify_hr_managers_digest(self, report_id: int, digest_text: str) -> None:
        hr_managers = User.objects.filter(role=User.Role.HR, is_active=True).exclude(username=SERVICE_USERNAME)
        if not hr_managers.exists():
            return

        try:
            payload = json.loads(digest_text)
            critical = payload.get('critical', [])
            warning = payload.get('warning', [])
            if not critical and not warning:
                # No Notification sent if zero insights
                return
            notif_type = 'WARNING' if critical else 'INFO'
        except Exception:
            notif_type = 'INFO'

        summary = self._extract_digest_summary(digest_text)
        for manager in hr_managers:
            Notification.objects.create(
                recipient=manager,
                type=notif_type,
                title='HR Agent Digest Ready',
                body=summary,
                link=f'/reports/{report_id}',
            )

        self.stdout.write(self.style.SUCCESS(
            f'Digest notifications sent to {hr_managers.count()} HR manager(s).'
        ))
