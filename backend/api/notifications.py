"""
Notification utility — plug this in anywhere to fire notifications.

Usage:
    from api.notifications import notify, notify_role

    # Single recipient
    notify(request.user, 'Your ticket was resolved', link='/it/tickets')

    # Everyone with a given role
    notify_role(User.Role.CEO, 'Low stock alert', body='Product X is out of stock',
                notification_type='WARNING', link='/inventory/low-stock-alert')
"""

from __future__ import annotations

from django.contrib.auth import get_user_model


def notify(recipient, title: str, body: str = '', notification_type: str = 'INFO', link: str = ''):
    """Create a single notification for one user."""
    from api.models import Notification
    return Notification.objects.create(
        recipient=recipient,
        title=title,
        body=body,
        type=notification_type,
        link=link,
    )


def notify_role(role: str, title: str, body: str = '', notification_type: str = 'INFO', link: str = ''):
    """Broadcast a notification to every active user with the given role."""
    from api.models import Notification
    User = get_user_model()
    recipients = User.objects.filter(role=role, is_active=True)
    Notification.objects.bulk_create([
        Notification(
            recipient=user,
            title=title,
            body=body,
            type=notification_type,
            link=link,
        )
        for user in recipients
    ])


def notify_many(recipients, title: str, body: str = '', notification_type: str = 'INFO', link: str = ''):
    """Broadcast a notification to an explicit queryset or list of users."""
    from api.models import Notification
    Notification.objects.bulk_create([
        Notification(
            recipient=user,
            title=title,
            body=body,
            type=notification_type,
            link=link,
        )
        for user in recipients
    ])
