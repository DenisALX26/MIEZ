import datetime
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


SEED_REPORTS = [
    {
        'name': 'Monthly Revenue Report',
        'slug': 'monthly-revenue',
        'category': 'Sales',
        'period': 'Feb 2026',
        'file_size_kb': 142,
        'generated_at': datetime.datetime(2026, 3, 1, 0, 0, 0, tzinfo=datetime.timezone.utc),
    },
    {
        'name': 'Quarterly Profit & Loss',
        'slug': 'quarterly-pl',
        'category': 'Finance',
        'period': 'Q3 FY26',
        'file_size_kb': 318,
        'generated_at': datetime.datetime(2026, 3, 1, 0, 0, 0, tzinfo=datetime.timezone.utc),
    },
    {
        'name': 'Inventory Stock Report',
        'slug': 'inventory-stock',
        'category': 'Inventory',
        'period': 'Feb 2026',
        'file_size_kb': 95,
        'generated_at': datetime.datetime(2026, 3, 1, 0, 0, 0, tzinfo=datetime.timezone.utc),
    },
    {
        'name': 'HR Headcount Summary',
        'slug': 'hr-headcount',
        'category': 'HR',
        'period': 'Feb 2026',
        'file_size_kb': 78,
        'generated_at': datetime.datetime(2026, 3, 1, 0, 0, 0, tzinfo=datetime.timezone.utc),
    },
    {
        'name': 'IT Ticket SLA Report',
        'slug': 'it-ticket-sla',
        'category': 'IT',
        'period': 'Feb 2026',
        'file_size_kb': 56,
        'generated_at': datetime.datetime(2026, 3, 1, 0, 0, 0, tzinfo=datetime.timezone.utc),
    },
    {
        'name': 'Sales Channel Analysis',
        'slug': 'sales-channel-analysis',
        'category': 'Sales',
        'period': 'Q3 FY26',
        'file_size_kb': 204,
        'generated_at': datetime.datetime(2026, 2, 28, 0, 0, 0, tzinfo=datetime.timezone.utc),
    },
    {
        'name': 'Employee Attendance Report',
        'slug': 'employee-attendance',
        'category': 'HR',
        'period': 'Feb 2026',
        'file_size_kb': 112,
        'generated_at': datetime.datetime(2026, 2, 28, 0, 0, 0, tzinfo=datetime.timezone.utc),
    },
    {
        'name': 'Top Customers Report',
        'slug': 'top-customers',
        'category': 'Sales',
        'period': 'Q3 FY26',
        'file_size_kb': 88,
        'generated_at': datetime.datetime(2026, 2, 25, 0, 0, 0, tzinfo=datetime.timezone.utc),
    },
    {
        'name': 'Annual Tax Summary',
        'slug': 'annual-tax-summary',
        'category': 'Finance',
        'period': 'FY25',
        'file_size_kb': 1200,
        'generated_at': datetime.datetime(2026, 2, 15, 0, 0, 0, tzinfo=datetime.timezone.utc),
    },
]


def seed_reports(apps, schema_editor):
    Report = apps.get_model('api', 'Report')
    Report.objects.all().delete()
    for data in SEED_REPORTS:
        Report.objects.create(**data)


class Migration(migrations.Migration):
    # atomic=False needed because PostgreSQL defers unique index creation to end
    # of transaction, which conflicts with the RunPython data seed in the same tx.
    atomic = False

    dependencies = [
        ('api', '0005_backfill_user_departments'),
    ]

    operations = [
        migrations.AddField(
            model_name='report',
            name='slug',
            field=models.SlugField(default='', max_length=100),
        ),
        migrations.AddField(
            model_name='report',
            name='file_size_kb',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='report',
            name='generated_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='report',
            name='generated_by',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='reports_generated',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name='report',
            name='slug',
            field=models.SlugField(max_length=100, unique=True),
        ),
        migrations.RunPython(seed_reports, migrations.RunPython.noop),
    ]
