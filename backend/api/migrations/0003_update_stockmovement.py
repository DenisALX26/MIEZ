from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_order_channel_order_date_order_value_ron_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='stockmovement',
            name='supplier',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='stock_movements', to='api.supplier'),
        ),
    ]
