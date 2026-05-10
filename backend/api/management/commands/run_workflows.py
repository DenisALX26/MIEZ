"""
Management command to evaluate and execute time-based workflow triggers.

Run once per minute via cron:
  * * * * * /app/manage.py run_workflows

Handles: DAILY_AT_TIME, WEEKLY_AT_TIME, CONTRACT_EXPIRES.

Note: workflows marked with trigger_config["managed_by"] are owned by a
dedicated management command (e.g. run_hr_agent) and are skipped here to
avoid double-execution.
"""
from __future__ import annotations

import logging

from django.core.management.base import BaseCommand
from django.utils import timezone

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Evaluate and run active time-based workflow triggers.'

    def handle(self, *args, **options):
        from api.models import Workflow
        from api.workflow_engine import execute_workflow

        now = timezone.localtime()
        current_time = now.strftime('%H:%M')
        current_day = now.strftime('%A').lower()

        self.stdout.write(
            f'[run_workflows] {now.isoformat()} — day={current_day}, time={current_time}'
        )

        triggered = 0

        for workflow in Workflow.objects.filter(is_active=True):
            if workflow.trigger_config.get('managed_by'):
                continue

            tt = workflow.trigger_type

            if tt == Workflow.TriggerType.DAILY_AT_TIME:
                if workflow.trigger_config.get('time') == current_time:
                    self._run(execute_workflow, workflow, tt, {
                        'scheduled_time': current_time,
                        'triggered_at': now.isoformat(),
                        'message': f'Daily workflow "{workflow.name}" triggered at {current_time}.',
                        'link': '/workflows',
                    })
                    triggered += 1

            elif tt == Workflow.TriggerType.WEEKLY_AT_TIME:
                scheduled_day = workflow.trigger_config.get('day_of_week', '').lower()
                if scheduled_day == current_day and workflow.trigger_config.get('time') == current_time:
                    self._run(execute_workflow, workflow, tt, {
                        'scheduled_day': current_day,
                        'scheduled_time': current_time,
                        'triggered_at': now.isoformat(),
                        'message': f'Weekly workflow "{workflow.name}" triggered on {current_day} at {current_time}.',
                        'link': '/workflows',
                    })
                    triggered += 1

            elif tt == Workflow.TriggerType.CONTRACT_EXPIRES:
                self._check_expiring_contracts(execute_workflow, workflow, now)
                triggered += 1

        self.stdout.write(self.style.SUCCESS(f'[run_workflows] done — {triggered} workflow(s) checked.'))

    def _run(self, execute_workflow, workflow, trigger_type, context):
        self.stdout.write(f'  Triggering "{workflow.name}" ({trigger_type})')
        try:
            execute_workflow(workflow, trigger_type, context)
        except Exception as exc:
            logger.exception('Workflow "%s" execution failed: %s', workflow.name, exc)

    def _check_expiring_contracts(self, execute_workflow, workflow, now):
        from datetime import timedelta
        from api.models import Contract

        days_ahead = int(workflow.trigger_config.get('days_ahead', 30))
        today = now.date()
        cutoff = today + timedelta(days=days_ahead)
        expiring = Contract.objects.filter(end_date__gte=today, end_date__lte=cutoff)

        if expiring.exists():
            self.stdout.write(f'  Triggering "{workflow.name}" — {expiring.count()} contract(s) expiring')
            context = {
                'expiring_count': expiring.count(),
                'days_ahead': days_ahead,
                'message': f'{expiring.count()} contract(s) expiring within {days_ahead} days.',
                'link': '/contracts',
            }
            try:
                execute_workflow(workflow, workflow.TriggerType.CONTRACT_EXPIRES, context)
            except Exception as exc:
                logger.exception('Workflow "%s" execution failed: %s', workflow.name, exc)
