from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0007_alter_report_slug'),
    ]

    operations = [
        migrations.AddField(
            model_name='ticket',
            name='category',
            field=models.CharField(blank=True, default='', max_length=80),
        ),
        migrations.AddField(
            model_name='ticket',
            name='requested_for',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='tickets_requested_for', to=settings.AUTH_USER_MODEL),
        ),
    ]
