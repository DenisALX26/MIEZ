from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('api', '0018_notification_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(
                choices=[
                    ('PROCESSING', 'Processing'),
                    ('SHIPPED', 'Shipped'),
                    ('DELIVERED', 'Delivered'),
                    ('CANCELLED', 'Cancelled'),
                ],
                default='PROCESSING',
                max_length=16,
            ),
        ),
    ]
