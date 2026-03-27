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
    department = models.ForeignKey(
        'Department',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='employees',
    )
    full_time = models.BooleanField(default=True)

    class Meta:
        db_table = 'users'


class Department(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True)
    icon = models.CharField(max_length=40, default='Building2')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self) -> str:
        return self.name