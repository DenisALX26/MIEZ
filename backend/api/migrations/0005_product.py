from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0004_user_address_user_employment_type_user_phone_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('sku', models.CharField(max_length=80, unique=True)),
                ('category', models.CharField(blank=True, default='', max_length=120)),
                ('stock_count', models.IntegerField(default=0)),
                ('min_stock', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
    ]
