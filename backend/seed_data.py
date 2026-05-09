import os
from datetime import timedelta
from decimal import Decimal

import django


# Allow running this as a standalone script: `python seed_data.py`
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone
from api.models import Department, SystemStatus


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
            "is_active": True,
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


def seed_products():
    from api.models import Product

    products = [
        {"name": "Widget A", "sku": "WIDGET-A", "category": "Electronics", "stock_count": 2, "min_stock": 5},
        {"name": "Widget B", "sku": "WIDGET-B", "category": "Accessories", "stock_count": 0, "min_stock": 10},
        {"name": "Gadget X", "sku": "GADGET-X", "category": "Electronics", "stock_count": 20, "min_stock": 5},
    ]

    # Build defaults/update dicts only with fields that exist on the current Product model
    field_names = {f.name for f in Product._meta.fields}

    for p in products:
        defaults = {}
        # only include keys that actually exist on the model
        for key in ('name', 'category', 'stock_count', 'min_stock', 'unit_price_ron'):
            if key in field_names and key in p:
                defaults[key] = p[key]

        prod, created = Product.objects.get_or_create(sku=p['sku'], defaults=defaults)
        if created:
            print(f"Created product: {prod.sku}")
        else:
            updated = False
            for key, val in defaults.items():
                if getattr(prod, key, None) != val:
                    setattr(prod, key, val)
                    updated = True
            if updated:
                prod.save()
                print(f"Updated product: {prod.sku}")
            else:
                print(f"Already up-to-date: {prod.sku}")


def seed_tickets():
    from api.models import Ticket

    it_department = Department.objects.filter(slug='it').first()

    requested_by_it = User.objects.filter(username='elena.vasile').first()
    assigned_to_it = User.objects.filter(username='ion.dragomir').first()
    requested_by_sales = User.objects.filter(username='mihai.popescu').first()

    tickets = [
        {
            'ticket_number': 'IT-1001',
            'title': 'Cannot connect to office VPN',
            'description': 'VPN client times out for remote employee.',
            'department': it_department,
            'priority': Ticket.Priority.HIGH,
            'status': Ticket.Status.OPEN,
            'requested_by': requested_by_sales,
            'assigned_to': assigned_to_it,
            'location': 'Bucharest HQ',
        },
        {
            'ticket_number': 'IT-1002',
            'title': 'Email attachments blocked',
            'description': 'Outgoing attachments are rejected by mail gateway.',
            'department': it_department,
            'priority': Ticket.Priority.MEDIUM,
            'status': Ticket.Status.IN_PROGRESS,
            'requested_by': requested_by_it,
            'assigned_to': assigned_to_it,
            'location': 'Cluj Office',
        },
        {
            'ticket_number': 'IT-1003',
            'title': 'Laptop blue screen after update',
            'description': 'Recurring BSOD after security patch installation.',
            'department': it_department,
            'priority': Ticket.Priority.URGENT,
            'status': Ticket.Status.OPEN,
            'requested_by': requested_by_it,
            'assigned_to': None,
            'location': 'Remote',
        },
        {
            'ticket_number': 'IT-1004',
            'title': 'Printer queue stalled on floor 2',
            'description': 'Jobs remain queued and never reach the printer.',
            'department': it_department,
            'priority': Ticket.Priority.LOW,
            'status': Ticket.Status.RESOLVED,
            'requested_by': requested_by_sales,
            'assigned_to': assigned_to_it,
            'location': 'Bucharest HQ',
        },
    ]

    for data in tickets:
        ticket, created = Ticket.objects.get_or_create(
            ticket_number=data['ticket_number'],
            defaults={
                'title': data['title'],
                'description': data['description'],
                'department': data['department'],
                'priority': data['priority'],
                'status': data['status'],
                'requested_by': data['requested_by'],
                'assigned_to': data['assigned_to'],
                'location': data['location'],
            },
        )

        if created:
            print(f"Created ticket: {ticket.ticket_number}")
        else:
            ticket.title = data['title']
            ticket.description = data['description']
            ticket.department = data['department']
            ticket.priority = data['priority']
            ticket.status = data['status']
            ticket.requested_by = data['requested_by']
            ticket.assigned_to = data['assigned_to']
            ticket.location = data['location']
            ticket.save()
            print(f"Updated ticket: {ticket.ticket_number}")


def seed_sales_orders():
    from api.models import Customer, Order, OrderItem, Product

    # Sales rep owner for created_by fields in seeded orders
    sales_owner = User.objects.filter(username='mihai.popescu').first()

    customers = [
        {
            'name': 'Acme SRL',
            'contact_email': 'orders@acme.ro',
            'contact_phone': '+40700111222',
            'location': 'Bucharest',
        },
        {
            'name': 'Beta Retail',
            'contact_email': 'supply@beta.ro',
            'contact_phone': '+40700333444',
            'location': 'Cluj-Napoca',
        },
        {
            'name': 'Carpathia Direct',
            'contact_email': 'sales@carpathia.ro',
            'contact_phone': '+40700555666',
            'location': 'Timisoara',
        },
    ]

    customer_map = {}
    for customer_data in customers:
        customer, _ = Customer.objects.get_or_create(
            name=customer_data['name'],
            defaults={
                'contact_email': customer_data['contact_email'],
                'contact_phone': customer_data['contact_phone'],
                'location': customer_data['location'],
            },
        )
        customer_map[customer.name] = customer

    # Ensure product fixtures used for order line items exist.
    product_defaults = {
        'WIDGET-A': {'name': 'Widget A', 'category': Product.Category.ELECTRONICS},
        'WIDGET-B': {'name': 'Widget B', 'category': Product.Category.ACCESSORIES},
        'GADGET-X': {'name': 'Gadget X', 'category': Product.Category.ELECTRONICS},
    }

    products = {}
    for sku, defaults in product_defaults.items():
        product, _ = Product.objects.get_or_create(
            sku=sku,
            defaults={
                'name': defaults['name'],
                'category': defaults['category'],
                'unit_price_ron': Decimal('10.00'),
            },
        )
        products[sku] = product

    today = timezone.localdate()
    yesterday = today - timedelta(days=1)
    two_days_ago = today - timedelta(days=2)
    start_of_week = today - timedelta(days=today.weekday())
    previous_week = start_of_week - timedelta(days=1)

    orders = [
        {
            'order_number': '#2001',
            'customer': 'Acme SRL',
            'value_ron': Decimal('120.50'),
            'date': today,
            'status': Order.Status.PROCESSING,
            'channel': Order.Channel.WEBSITE,
            'items': [
                {'sku': 'WIDGET-A', 'quantity': 2, 'unit_price_ron': Decimal('30.00')},
                {'sku': 'WIDGET-B', 'quantity': 1, 'unit_price_ron': Decimal('60.50')},
            ],
        },
        {
            'order_number': '#2002',
            'customer': 'Beta Retail',
            'value_ron': Decimal('80.00'),
            'date': today,
            'status': Order.Status.PENDING,
            'channel': Order.Channel.EMAG,
            'items': [
                {'sku': 'WIDGET-A', 'quantity': 1, 'unit_price_ron': Decimal('80.00')},
            ],
        },
        {
            'order_number': '#2003',
            'customer': 'Acme SRL',
            'value_ron': Decimal('45.00'),
            'date': yesterday,
            'status': Order.Status.DELIVERED,
            'channel': Order.Channel.DIRECT,
            'items': [
                {'sku': 'GADGET-X', 'quantity': 3, 'unit_price_ron': Decimal('15.00')},
            ],
        },
        {
            'order_number': '#2004',
            'customer': 'Carpathia Direct',
            'value_ron': Decimal('30.00'),
            'date': yesterday,
            'status': Order.Status.RETURNED,
            'channel': Order.Channel.WEBSITE,
            'items': [
                {'sku': 'WIDGET-B', 'quantity': 1, 'unit_price_ron': Decimal('30.00')},
            ],
        },
        {
            'order_number': '#2005',
            'customer': 'Beta Retail',
            'value_ron': Decimal('60.00'),
            'date': two_days_ago,
            'status': Order.Status.SHIPPED,
            'channel': Order.Channel.EMAG,
            'items': [
                {'sku': 'GADGET-X', 'quantity': 2, 'unit_price_ron': Decimal('30.00')},
            ],
        },
        {
            'order_number': '#2006',
            'customer': 'Acme SRL',
            'value_ron': Decimal('20.00'),
            'date': start_of_week,
            'status': Order.Status.RETURNED,
            'channel': Order.Channel.DIRECT,
            'items': [
                {'sku': 'WIDGET-A', 'quantity': 1, 'unit_price_ron': Decimal('20.00')},
            ],
        },
        {
            'order_number': '#2007',
            'customer': 'Beta Retail',
            'value_ron': Decimal('15.00'),
            'date': previous_week,
            'status': Order.Status.RETURNED,
            'channel': Order.Channel.WEBSITE,
            'items': [
                {'sku': 'WIDGET-B', 'quantity': 1, 'unit_price_ron': Decimal('15.00')},
            ],
        },
    ]

    for payload in orders:
        order, created = Order.objects.get_or_create(
            order_number=payload['order_number'],
            defaults={
                'customer': customer_map[payload['customer']],
                'created_by': sales_owner,
                'value_ron': payload['value_ron'],
                'date': payload['date'],
                'status': payload['status'],
                'channel': payload['channel'],
            },
        )

        if not created:
            order.customer = customer_map[payload['customer']]
            order.created_by = sales_owner
            order.value_ron = payload['value_ron']
            order.date = payload['date']
            order.status = payload['status']
            order.channel = payload['channel']
            order.save()

        keep_ids = []
        for item in payload['items']:
            line, _ = OrderItem.objects.update_or_create(
                order=order,
                product=products[item['sku']],
                defaults={
                    'quantity': item['quantity'],
                    'unit_price_ron': item['unit_price_ron'],
                },
            )
            keep_ids.append(line.id)

        OrderItem.objects.filter(order=order).exclude(id__in=keep_ids).delete()

        print(f"{'Created' if created else 'Updated'} order: {order.order_number}")


def seed_systems():
    systems = [
        {
            'name': 'Database Server',
            'uptime_pct': Decimal('99.98'),
            'status': SystemStatus.StatusChoices.ONLINE,
            'last_incident_date': None,
        },
        {
            'name': 'API Server',
            'uptime_pct': Decimal('99.95'),
            'status': SystemStatus.StatusChoices.ONLINE,
            'last_incident_date': None,
        },
        {
            'name': 'Frontend CDN',
            'uptime_pct': Decimal('98.50'),
            'status': SystemStatus.StatusChoices.DEGRADED,
            'last_incident_date': timezone.make_aware(timezone.datetime(2024, 1, 15, 10, 30, 0)),
        },
        {
            'name': 'Email Service',
            'uptime_pct': Decimal('95.00'),
            'status': SystemStatus.StatusChoices.DEGRADED,
            'last_incident_date': timezone.make_aware(timezone.datetime(2024, 1, 18, 14, 20, 0)),
        },
    ]

    for system_data in systems:
        system, created = SystemStatus.objects.update_or_create(
            name=system_data['name'],
            defaults={
                'uptime_pct': system_data['uptime_pct'],
                'status': system_data['status'],
                'last_incident_date': system_data['last_incident_date'],
            }
        )
        status_msg = 'Created' if created else 'Updated'
        print(f'{status_msg} system: {system.name} - {system.status}')

    print('System status data seeded successfully!')


def seed_reports():
    from api.models import Report
    from django.utils.text import slugify
    from pathlib import Path
    import csv
    from io import StringIO

    ceo_user = User.objects.filter(username='admin').first()
    
    # Ensure reports directory exists
    reports_dir = Path('/app/reports')
    reports_dir.mkdir(exist_ok=True)

    # Template data for different report types
    report_templates = {
        'q4-sales-report': {
            'headers': ['Month', 'Sales Target (RON)', 'Actual Sales (RON)', 'Achievement %', 'Units Sold'],
            'rows': [
                ['October 2024', '500000', '520000', '104%', '1250'],
                ['November 2024', '520000', '545000', '105%', '1340'],
                ['December 2024', '550000', '580000', '105%', '1420'],
                ['TOTAL Q4', '1570000', '1645000', '105%', '4010'],
            ]
        },
        'monthly-finance-summary': {
            'headers': ['Category', 'Budget (RON)', 'Actual (RON)', 'Variance (RON)', 'Variance %'],
            'rows': [
                ['Revenue', '1570000', '1645000', '+75000', '+4.8%'],
                ['Cost of Goods', '785000', '802000', '-17000', '-2.2%'],
                ['Operating Expenses', '400000', '398000', '+2000', '+0.5%'],
                ['Net Income', '385000', '445000', '+60000', '+15.6%'],
            ]
        },
        'inventory-movement-analysis': {
            'headers': ['Product', 'Opening Stock', 'Inbound', 'Outbound', 'Closing Stock', 'Status'],
            'rows': [
                ['Widget A', '150', '200', '220', '130', 'Low'],
                ['Widget B', '85', '150', '100', '135', 'Normal'],
                ['Gadget X', '500', '300', '450', '350', 'Normal'],
                ['Gadget Y', '200', '250', '300', '150', 'Low'],
                ['Tool Z', '400', '100', '120', '380', 'Normal'],
            ]
        },
        'employee-attendance': {
            'headers': ['Department', 'Total Employees', 'Present', 'Absent', 'Remote', 'Leave', 'Attendance %'],
            'rows': [
                ['HR', '2', '2', '0', '0', '0', '100%'],
                ['Sales', '3', '2', '0', '1', '0', '100%'],
                ['IT', '2', '1', '0', '1', '0', '100%'],
                ['Inventory', '1', '1', '0', '0', '0', '100%'],
                ['TOTAL', '8', '6', '0', '2', '0', '100%'],
            ]
        },
        'it-support-tickets-summary': {
            'headers': ['Priority', 'Open', 'In Progress', 'Resolved', 'Closed', 'Avg Resolution Time'],
            'rows': [
                ['Urgent', '1', '2', '15', '2', '2.5 hours'],
                ['High', '3', '4', '28', '8', '6 hours'],
                ['Medium', '8', '5', '42', '15', '12 hours'],
                ['Low', '12', '3', '38', '20', '24 hours'],
                ['TOTAL', '24', '14', '123', '45', '11 hours'],
            ]
        },
        'revenue-by-channel': {
            'headers': ['Channel', 'Orders', 'Revenue (RON)', 'Avg Order Value', 'Growth %'],
            'rows': [
                ['eMAG', '450', '675000', '1500', '+12%'],
                ['Website', '320', '520000', '1625', '+8%'],
                ['Direct Sales', '145', '350000', '2414', '+15%'],
                ['TOTAL', '915', '1545000', '1688', '+11%'],
            ]
        },
        'budget-vs-actual': {
            'headers': ['Quarter', 'Budget (RON)', 'Actual (RON)', 'Difference', 'Status'],
            'rows': [
                ['Q1 2024', '1200000', '1185000', '-15000', 'Under'],
                ['Q2 2024', '1300000', '1325000', '+25000', 'Over'],
                ['Q3 2024', '1450000', '1468000', '+18000', 'Over'],
                ['Q4 2024 (Est)', '1570000', '1645000', '+75000', 'Over'],
                ['FULL YEAR', '5520000', '5623000', '+103000', 'Over'],
            ]
        },
        'stock-levels-report': {
            'headers': ['Product SKU', 'Current Stock', 'Min Stock Level', 'Status', 'Reorder Qty', 'Days to Stockout'],
            'rows': [
                ['WIDGET-A', '130', '50', 'Low', '200', '15'],
                ['WIDGET-B', '135', '40', 'Normal', '0', '45'],
                ['GADGET-X', '350', '100', 'Normal', '0', '60'],
                ['GADGET-Y', '150', '75', 'Low', '150', '20'],
                ['TOOL-Z', '380', '100', 'Normal', '0', '90'],
            ]
        },
        'payroll-report': {
            'headers': ['Employee', 'Department', 'Gross Salary (RON)', 'Deductions (RON)', 'Net Salary (RON)', 'Status'],
            'rows': [
                ['Admin MIEZ', 'CEO', '8500', '2040', '6460', 'Processed'],
                ['Ana Mihai', 'HR', '4200', '1008', '3192', 'Processed'],
                ['Mihai Popescu', 'Sales', '5000', '1200', '3800', 'Processed'],
                ['Elena Vasile', 'IT', '6000', '1440', '4560', 'Processed'],
                ['TOTAL PAYROLL', '-', '23700', '5688', '18012', 'Completed'],
            ]
        },
    }

    reports = [
        {
            'name': 'Q4 Sales Report',
            'category': Report.Category.SALES,
            'period': 'Oct-Dec 2024',
            'file_size_kb': 245,
            'generated_at': timezone.now() - timedelta(days=5),
            'slug': 'q4-sales-report',
        },
        {
            'name': 'Monthly Finance Summary',
            'category': Report.Category.FINANCE,
            'period': 'December 2024',
            'file_size_kb': 156,
            'generated_at': timezone.now() - timedelta(days=2),
            'slug': 'monthly-finance-summary',
        },
        {
            'name': 'Inventory Movement Analysis',
            'category': Report.Category.INVENTORY,
            'period': 'Oct-Dec 2024',
            'file_size_kb': 312,
            'generated_at': timezone.now() - timedelta(days=10),
            'slug': 'inventory-movement-analysis',
        },
        {
            'name': 'Employee Attendance',
            'category': Report.Category.HR,
            'period': 'December 2024',
            'file_size_kb': 89,
            'generated_at': timezone.now() - timedelta(days=1),
            'slug': 'employee-attendance',
        },
        {
            'name': 'IT Support Tickets Summary',
            'category': Report.Category.IT,
            'period': 'Q4 2024',
            'file_size_kb': 201,
            'generated_at': timezone.now() - timedelta(days=7),
            'slug': 'it-support-tickets-summary',
        },
        {
            'name': 'Revenue by Channel',
            'category': Report.Category.SALES,
            'period': 'November 2024',
            'file_size_kb': 178,
            'generated_at': timezone.now() - timedelta(days=15),
            'slug': 'revenue-by-channel',
        },
        {
            'name': 'Budget vs Actual',
            'category': Report.Category.FINANCE,
            'period': 'Q4 2024',
            'file_size_kb': 267,
            'generated_at': timezone.now() - timedelta(days=20),
            'slug': 'budget-vs-actual',
        },
        {
            'name': 'Stock Levels Report',
            'category': Report.Category.INVENTORY,
            'period': 'December 2024',
            'file_size_kb': 134,
            'generated_at': timezone.now() - timedelta(days=3),
            'slug': 'stock-levels-report',
        },
        {
            'name': 'Payroll Report',
            'category': Report.Category.HR,
            'period': 'December 2024',
            'file_size_kb': 95,
            'generated_at': timezone.now() - timedelta(days=4),
            'slug': 'payroll-report',
        },
    ]

    for data in reports:
        # Create a realistic CSV file for each report
        file_path = reports_dir / f"{data['slug']}.csv"
        
        template = report_templates.get(data['slug'], {
            'headers': ['Column 1', 'Column 2', 'Column 3'],
            'rows': [['Data 1', 'Data 2', 'Data 3']]
        })
        
        # Write CSV file
        with open(file_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(template['headers'])
            writer.writerows(template['rows'])
        
        report, created = Report.objects.get_or_create(
            slug=data['slug'],
            defaults={
                'name': data['name'],
                'category': data['category'],
                'period': data['period'],
                'file_size_kb': data['file_size_kb'],
                'generated_at': data['generated_at'],
                'generated_by': ceo_user,
                'file_path': str(file_path),
            },
        )
        if created:
            print(f"Created report: {report.name} ({report.category})")
        else:
            report.name = data['name']
            report.category = data['category']
            report.period = data['period']
            report.file_size_kb = data['file_size_kb']
            report.generated_at = data['generated_at']
            report.generated_by = ceo_user
            report.file_path = str(file_path)
            report.save()
            print(f"Updated report: {report.name}")

    print('Report data seeded successfully!')


if __name__ == "__main__":
    seed_users()
    seed_products()
    seed_sales_orders()
    seed_tickets()
    seed_systems()
    seed_reports()