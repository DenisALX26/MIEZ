from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    class Role(models.TextChoices):
        CEO = 'CEO', 'CEO'
        HR = 'HR', 'HR'
        SALES = 'SALES', 'Sales Rep'
        IT = 'IT', 'IT Technician'
        INVENTORY = 'INVENTORY', 'Inventory Manager'

    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.CEO
    )

    class Meta:
        db_table = 'users'