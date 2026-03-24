from django.contrib.auth import get_user_model

User = get_user_model()

def seed_users():
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
        },
        {
            "username": "ana.mihai",
            "email": "ana.mihai@miez.ro",
            "first_name": "Ana",
            "last_name": "Mihai",
            "password": "password",
            "role": "HR",
        },
        {
            "username": "mihai.popescu",
            "email": "mihai.popescu@miez.ro",
            "first_name": "Mihai",
            "last_name": "Popescu",
            "password": "password",
            "role": "SALES",
        },
        {
            "username": "radu.pop",
            "email": "radu.pop@miez.ro",
            "first_name": "Radu",
            "last_name": "Pop",
            "password": "password",
            "role": "SALES",
        },
        {
            "username": "elena.vasile",
            "email": "elena.vasile@miez.ro",
            "first_name": "Elena",
            "last_name": "Vasile",
            "password": "password",
            "role": "IT",
        },
        {
            "username": "ion.dragomir",
            "email": "ion.dragomir@miez.ro",
            "first_name": "Ion",
            "last_name": "Dragomir",
            "password": "password",
            "role": "IT",
        },
        {
            "username": "andrei.negrescu",
            "email": "andrei.negrescu@miez.ro",
            "first_name": "Andrei",
            "last_name": "Negrescu",
            "password": "password",
            "role": "SALES",
        },
        {
            "username": "cristina.ionescu",
            "email": "cristina.ionescu@miez.ro",
            "first_name": "Cristina",
            "last_name": "Ionescu",
            "password": "password",
            "role": "HR",
        },
        {
            "username": "maria.stanciu",
            "email": "maria.stanciu@miez.ro",
            "first_name": "Maria",
            "last_name": "Stanciu",
            "password": "password",
            "role": "SALES",
            "is_active": False,
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
            }
        )
        if created:
            user.set_password(data["password"])
            user.save()
            print(f"Created user: {user.username} ({user.role})")
        else:
            print(f"Already exists: {user.username}")