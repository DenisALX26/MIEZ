import os

import django


# Allow running this as a standalone script: `python seed_data.py`
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from django.contrib.auth import get_user_model
from api.models import Department


User = get_user_model()

def seed_users():
    departments = {
        'HR': Department.objects.get_or_create(
            slug='hr',
            defaults={'name': 'Human Resources', 'icon': 'Users'},
        )[0],
        'SALES': Department.objects.get_or_create(
            slug='sales',
            defaults={'name': 'Sales', 'icon': 'BarChart3'},
        )[0],
        'IT': Department.objects.get_or_create(
            slug='it',
            defaults={'name': 'IT', 'icon': 'Monitor'},
        )[0],
        'INVENTORY': Department.objects.get_or_create(
            slug='inventory',
            defaults={'name': 'Inventory', 'icon': 'Package'},
        )[0],
    }

    users = [
        {
            "username": "admin",
            "email": "admin@miez.ro",
            "first_name": "Admin",
            "last_name": "MIEZ",
            "password": "password",
            "role": "CEO",
            "is_staff": True,
            "is_superuser": True,
            "full_time": True,
        },
        {
            "username": "ana.mihai",
            "email": "ana.mihai@miez.ro",
            "first_name": "Ana",
            "last_name": "Mihai",
            "password": "password",
            "role": "HR",
            "full_time": True,
        },
        {
            "username": "mihai.popescu",
            "email": "mihai.popescu@miez.ro",
            "first_name": "Mihai",
            "last_name": "Popescu",
            "password": "password",
            "role": "SALES",
            "full_time": True,
        },
        {
            "username": "radu.pop",
            "email": "radu.pop@miez.ro",
            "first_name": "Radu",
            "last_name": "Pop",
            "password": "password",
            "role": "SALES",
            "full_time": False,
        },
        {
            "username": "elena.vasile",
            "email": "elena.vasile@miez.ro",
            "first_name": "Elena",
            "last_name": "Vasile",
            "password": "password",
            "role": "IT",
            "full_time": True,
        },
        {
            "username": "ion.dragomir",
            "email": "ion.dragomir@miez.ro",
            "first_name": "Ion",
            "last_name": "Dragomir",
            "password": "password",
            "role": "IT",
            "full_time": False,
        },
        {
            "username": "andrei.negrescu",
            "email": "andrei.negrescu@miez.ro",
            "first_name": "Andrei",
            "last_name": "Negrescu",
            "password": "password",
            "role": "SALES",
            "full_time": True,
        },
        {
            "username": "cristina.ionescu",
            "email": "cristina.ionescu@miez.ro",
            "first_name": "Cristina",
            "last_name": "Ionescu",
            "password": "password",
            "role": "HR",
            "full_time": True,
        },
        {
            "username": "maria.stanciu",
            "email": "maria.stanciu@miez.ro",
            "first_name": "Maria",
            "last_name": "Stanciu",
            "password": "password",
            "role": "SALES",
            "is_active": False,
            "full_time": False,
        },
        {
            "username": "darius.sava",
            "email": "darius.sava@miez.ro",
            "first_name": "Darius",
            "last_name": "Sava",
            "password": "password",
            "role": "INVENTORY",
            "is_active": False,
            "full_time": False,
        },
    ]

    for data in users:
        user, created = User.objects.get_or_create(
            username=data["username"],
            defaults={
                "email": data["email"],
                "first_name": data["first_name"],
                "last_name": data["last_name"],
                "role": data["role"],
                "is_staff": data.get("is_staff", False),
                "is_superuser": data.get("is_superuser", False),
                "is_active": data.get("is_active", True),
                "full_time": data.get("full_time", True),
                "department": departments.get(data["role"]),
            }
        )
        if created:
            user.set_password(data["password"])
            user.save()
            print(f"Created user: {user.username} ({user.role})")
        else:
            user.email = data["email"]
            user.first_name = data["first_name"]
            user.last_name = data["last_name"]
            user.role = data["role"]
            user.is_staff = data.get("is_staff", False)
            user.is_superuser = data.get("is_superuser", False)
            user.is_active = data.get("is_active", True)
            user.full_time = data.get("full_time", True)
            user.department = departments.get(data["role"])
            user.set_password(data["password"])
            user.save()
            print(f"Already exists: {user.username}")


if __name__ == "__main__":
    seed_users()