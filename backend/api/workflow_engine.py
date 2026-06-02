"""
Workflow execution engine.

execute_workflow(workflow, trigger_type, context) runs a workflow's actions
sequentially, logs each result, and writes a WorkflowLog entry.
A failed action is recorded but does not stop subsequent actions.
"""
from __future__ import annotations

import logging
from typing import Any

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

logger = logging.getLogger(__name__)


# ── Email helper ─────────────────────────────────────────────────────────────

def _email_configured() -> bool:
    """True when an SMTP host is configured (so we should actually send)."""
    return bool(getattr(settings, 'EMAIL_HOST', ''))


def _send_email(subject: str, body: str, recipients: list[str]) -> str:
    """Send an email to the given addresses via the configured backend.

    Returns a human-readable status string for the workflow action log. Degrades
    gracefully: when no recipient address is resolvable or SMTP is not
    configured it records that instead of raising, so the workflow still
    succeeds in dev environments without email set up.
    """
    clean = sorted({(r or '').strip() for r in recipients if (r or '').strip()})
    if not clean:
        return 'no recipient email address available'
    if not _email_configured():
        return f'email backend not configured — would email {len(clean)} recipient(s)'

    from_email = (
        getattr(settings, 'DEFAULT_FROM_EMAIL', '')
        or getattr(settings, 'EMAIL_HOST_USER', '')
        or 'no-reply@miez.local'
    )
    send_mail(subject, body, from_email, clean, fail_silently=False)
    return f'emailed {len(clean)} recipient(s): {", ".join(clean)}'


def execute_workflow(workflow, trigger_type: str, context: dict[str, Any]) -> dict:
    """Execute all actions in a workflow and persist a WorkflowLog entry."""
    from api.models import WorkflowLog

    actions_log: list[dict] = []
    overall_success = True

    for action_type in (workflow.actions or []):
        result = _dispatch_action(action_type, workflow, context)
        actions_log.append(result)
        if not result['success']:
            overall_success = False
            logger.warning(
                'Workflow %s: action %s failed — %s',
                workflow.name, action_type, result.get('message'),
            )

    workflow.last_triggered_at = timezone.now()
    workflow.save(update_fields=['last_triggered_at'])

    WorkflowLog.objects.create(
        workflow=workflow,
        trigger_type=trigger_type,
        actions_log=actions_log,
        success=overall_success,
    )

    return {'success': overall_success, 'actions_log': actions_log}


def _dispatch_action(action_type: str, workflow, context: dict) -> dict:
    handlers = {
        'NOTIFY_MANAGER':           _notify_manager,
        'EMAIL_CEO':                _email_ceo,
        'EMAIL_SUPPLIER':           _email_supplier,
        'SEND_CONFIRMATION_EMAIL':  _send_confirmation_email,
        'UPDATE_DASHBOARD':         _update_dashboard,
        'GENERATE_REPORT':          _generate_report,
        'ASSIGN_TO_TEAM_LEAD':      _assign_to_team_lead,
        'POST_TO_CHANNEL':          _post_to_channel,
        'LOG_TO_AUDIT_TRAIL':       _log_to_audit_trail,
    }
    handler = handlers.get(action_type)
    if handler is None:
        return {'action': action_type, 'success': False, 'message': f'Unknown action type: {action_type}'}

    try:
        message = handler(workflow, context)
        return {'action': action_type, 'success': True, 'message': message}
    except Exception as exc:
        logger.exception('Action %s failed for workflow %s', action_type, workflow.name)
        return {'action': action_type, 'success': False, 'message': str(exc)}


# ── Action handlers ──────────────────────────────────────────────────────────

def _notify_manager(workflow, context: dict) -> str:
    from api.models import Notification, User
    managers = User.objects.filter(role__in=('HR', 'CEO'), is_active=True)
    body = context.get('message', f'Workflow "{workflow.name}" was triggered.')
    link = context.get('link', '/workflows')
    for m in managers:
        Notification.objects.create(recipient=m, title=f'Workflow: {workflow.name}', body=body, link=link)
    return f'Notified {managers.count()} manager(s)'


# Always cc'd on CEO workflow emails for demo purposes.
DEMO_CEO_EMAIL = 'petru.draghiceanu@gmail.com'


def _email_ceo(workflow, context: dict) -> str:
    from api.models import Notification, User
    ceos = list(User.objects.filter(role='CEO', is_active=True))
    body = context.get('message', f'Workflow "{workflow.name}" was triggered.')
    link = context.get('link', '/workflows')
    subject = context.get('subject', f'[MIEZ Workflow] {workflow.name}')
    for ceo in ceos:
        Notification.objects.create(recipient=ceo, title=f'[Workflow] {workflow.name}', body=body, link=link)
    recipients = [ceo.email for ceo in ceos] + [DEMO_CEO_EMAIL]
    email_status = _send_email(subject, body, recipients)
    return f'Notified {len(ceos)} CEO(s) in-app; {email_status}'


def _email_supplier(workflow, context: dict) -> str:
    from api.models import Supplier
    supplier = None
    if context.get('supplier_id'):
        supplier = Supplier.objects.filter(id=context['supplier_id']).first()
    if supplier is None and context.get('supplier_name'):
        supplier = Supplier.objects.filter(name__iexact=context['supplier_name']).first()

    address = context.get('supplier_email') or (supplier.contact_email if supplier else '')
    name = supplier.name if supplier else context.get('supplier_name', 'unknown supplier')
    subject = context.get('subject', f'[MIEZ] {workflow.name}')
    body = context.get('message', f'Automated message from workflow "{workflow.name}".')
    email_status = _send_email(subject, body, [address])
    return f'Supplier "{name}": {email_status}'


def _send_confirmation_email(workflow, context: dict) -> str:
    from api.models import Notification, User
    body = context.get('message', f'Confirmation from workflow "{workflow.name}".')
    link = context.get('link', '/')
    subject = context.get('subject', f'Confirmation: {workflow.name}')

    recipients: list[str] = []
    target = context.get('recipient_email') or 'unknown'
    if context.get('recipient_email'):
        recipients.append(context['recipient_email'])

    user = User.objects.filter(id=context['user_id']).first() if context.get('user_id') else None
    if user:
        Notification.objects.create(recipient=user, title=f'Confirmation: {workflow.name}', body=body, link=link)
        recipients.append(user.email)
        target = user.username

    email_status = _send_email(subject, body, recipients)
    return f'Confirmation for {target}: {email_status}'


def _update_dashboard(workflow, context: dict) -> str:
    return 'Dashboard update noted'


def _generate_report(workflow, context: dict) -> str:
    return 'Report generation queued'


def _assign_to_team_lead(workflow, context: dict) -> str:
    from api.models import Ticket, User
    ticket_id = context.get('ticket_id')
    if not ticket_id:
        return 'No ticket_id in context'
    try:
        ticket = Ticket.objects.get(id=ticket_id)
        lead = User.objects.filter(role='IT', is_active=True).first()
        if lead:
            ticket.assigned_to = lead
            ticket.save(update_fields=['assigned_to'])
            return f'Ticket #{ticket_id} assigned to {lead.username}'
        return 'No IT user found to assign'
    except Ticket.DoesNotExist:
        return f'Ticket #{ticket_id} not found'


def _post_to_channel(workflow, context: dict) -> str:
    from api.models import Notification, User
    users = User.objects.filter(is_active=True)
    body = context.get('message', f'Workflow "{workflow.name}" triggered.')
    link = context.get('link', '/workflows')
    for u in users:
        Notification.objects.create(recipient=u, title=f'[Channel] {workflow.name}', body=body, link=link)
    return f'Posted to channel — {users.count()} users notified'


def _log_to_audit_trail(workflow, context: dict) -> str:
    return f'Audit: workflow "{workflow.name}" triggered at {timezone.now().isoformat()}'
