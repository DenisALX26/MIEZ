from django.db import migrations


def forwards(apps, schema_editor):
    # Intentionally left blank.
    # Existing users must keep the department they were originally assigned.
    return


def backwards(apps, schema_editor):
    return


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0004_product_min_stock_alter_stockmovement_movement_type'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]