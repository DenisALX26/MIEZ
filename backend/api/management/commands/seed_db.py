"""
Comprehensive database seeder — covers every model with realistic demo data.
Run: python manage.py seed_db
"""
from datetime import date, timedelta, datetime, timezone as tz
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from api.models import (
    Attendance, Contract, Customer, Department, Invoice,
    LeaveRequest, Notification, Order, OrderItem, PayrollEntry,
    Product, Report, StockMovement, Supplier, Ticket, TicketComment,
    User, Workflow, WorkflowLog,
)

TODAY = date(2026, 4, 20)


def ago(days: int) -> date:
    return TODAY - timedelta(days=days)


def dt(d: date, hour: int = 9, minute: int = 0) -> datetime:
    return datetime(d.year, d.month, d.day, hour, minute, tzinfo=tz.utc)


def workdays(start: date, end: date):
    """Yield every weekday between start and end inclusive."""
    current = start
    while current <= end:
        if current.weekday() < 5:
            yield current
        current += timedelta(days=1)


class Command(BaseCommand):
    help = 'Seed the database with comprehensive demo data'

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write('Clearing existing data…')
        self._clear()

        self.stdout.write('Departments…')
        depts = self._departments()

        self.stdout.write('Users…')
        users = self._users(depts)

        self.stdout.write('Customers…')
        customers = self._customers()

        self.stdout.write('Products…')
        products = self._products()

        self.stdout.write('Suppliers…')
        suppliers = self._suppliers()

        self.stdout.write('Stock movements…')
        self._stock_movements(products, suppliers, users)

        self.stdout.write('Orders & order items…')
        orders = self._orders(customers, users, products)

        self.stdout.write('Invoices…')
        self._invoices(orders, users)

        self.stdout.write('Attendance…')
        self._attendance(users)

        self.stdout.write('Leave requests…')
        self._leave_requests(users, depts)

        self.stdout.write('Contracts…')
        self._contracts(users, depts)

        self.stdout.write('Payroll…')
        self._payroll(users)

        self.stdout.write('Tickets & comments…')
        self._tickets(users, depts)

        self.stdout.write('Notifications…')
        self._notifications(users)

        self.stdout.write('Workflows…')
        self._workflows()

        self.stdout.write('Reports…')
        self._reports()

        self.stdout.write(self.style.SUCCESS('✓ Database seeded successfully'))

    # ──────────────────────────────────────────────────────────────
    # Clear
    # ──────────────────────────────────────────────────────────────

    def _clear(self):
        WorkflowLog.objects.all().delete()
        Workflow.objects.all().delete()
        Notification.objects.all().delete()
        TicketComment.objects.all().delete()
        Ticket.objects.all().delete()
        PayrollEntry.objects.all().delete()
        Contract.objects.all().delete()
        LeaveRequest.objects.all().delete()
        Attendance.objects.all().delete()
        Invoice.objects.all().delete()
        OrderItem.objects.all().delete()
        Order.objects.all().delete()
        StockMovement.objects.all().delete()
        Supplier.objects.all().delete()
        Product.objects.all().delete()
        Customer.objects.all().delete()
        Report.objects.all().delete()
        User.objects.all().delete()
        Department.objects.all().delete()

    # ──────────────────────────────────────────────────────────────
    # Departments
    # ──────────────────────────────────────────────────────────────

    def _departments(self):
        specs = [
            ('Information Technology', 'it',        'Monitor'),
            ('Human Resources',        'hr',         'Users'),
            ('Sales',                  'sales',      'BarChart3'),
            ('Inventory',              'inventory',  'Package'),
            ('Finance',                'finance',    'Building2'),
        ]
        depts = {}
        for name, slug, icon in specs:
            d = Department.objects.create(name=name, slug=slug, icon=icon)
            depts[slug] = d
        return depts

    # ──────────────────────────────────────────────────────────────
    # Users
    # ──────────────────────────────────────────────────────────────

    def _users(self, depts):
        def make(username, email, first, last, role, dept_slug, position,
                 salary, phone, start, emp_type=User.EmploymentType.FULL_TIME,
                 is_staff=False, is_superuser=False):
            u = User.objects.create_user(
                username=username, email=email,
                password='password123',
                first_name=first, last_name=last,
                role=role,
                department=depts.get(dept_slug),
                position=position,
                salary_ron=Decimal(str(salary)),
                phone=phone,
                start_date=start,
                employment_type=emp_type,
                is_staff=is_staff,
                is_superuser=is_superuser,
            )
            return u

        it  = depts['it']
        hr  = depts['hr']
        sal = depts['sales']
        inv = depts['inventory']

        users = {}

        users['ceo'] = make('admin', 'admin@miez.ro', 'Andrei', 'Constantin',
                            User.Role.CEO, None, 'Chief Executive Officer',
                            35000, '+40 700 000 001', ago(1825),
                            is_staff=True, is_superuser=True)

        users['hr1'] = make('maria_pop', 'maria.pop@miez.ro', 'Maria', 'Pop',
                            User.Role.HR, 'hr', 'HR Manager', 12000,
                            '+40 700 100 001', ago(730))

        users['hr2'] = make('ana_ionescu', 'ana.ionescu@miez.ro', 'Ana', 'Ionescu',
                            User.Role.HR, 'hr', 'HR Specialist', 8500,
                            '+40 700 100 002', ago(400))

        users['it1'] = make('alex_stan', 'alex.stan@miez.ro', 'Alexandru', 'Stan',
                            User.Role.IT, 'it', 'IT Lead', 14000,
                            '+40 700 200 001', ago(900))

        users['it2'] = make('dan_radu', 'dan.radu@miez.ro', 'Dan', 'Radu',
                            User.Role.IT, 'it', 'Systems Administrator', 11000,
                            '+40 700 200 002', ago(500))

        users['it3'] = make('mihai_gheorghe', 'mihai.gheorghe@miez.ro', 'Mihai', 'Gheorghe',
                            User.Role.IT, 'it', 'IT Support Technician', 8000,
                            '+40 700 200 003', ago(200))

        users['sales1'] = make('elena_munteanu', 'elena.munteanu@miez.ro', 'Elena', 'Munteanu',
                               User.Role.SALES, 'sales', 'Senior Sales Representative', 10000,
                               '+40 700 300 001', ago(800))

        users['sales2'] = make('bogdan_popa', 'bogdan.popa@miez.ro', 'Bogdan', 'Popa',
                               User.Role.SALES, 'sales', 'Sales Representative', 7500,
                               '+40 700 300 002', ago(365))

        users['sales3'] = make('cristina_moldovan', 'cristina.moldovan@miez.ro', 'Cristina', 'Moldovan',
                               User.Role.SALES, 'sales', 'Sales Representative', 7500,
                               '+40 700 300 003', ago(300))

        users['sales4'] = make('andrei_stoica', 'andrei.stoica@miez.ro', 'Andrei', 'Stoica',
                               User.Role.SALES, 'sales', 'Junior Sales Representative', 6000,
                               '+40 700 300 004', ago(90))

        users['inv1'] = make('ioana_dumitrescu', 'ioana.dumitrescu@miez.ro', 'Ioana', 'Dumitrescu',
                             User.Role.INVENTORY, 'inventory', 'Inventory Manager', 11000,
                             '+40 700 400 001', ago(600))

        users['inv2'] = make('radu_costescu', 'radu.costescu@miez.ro', 'Radu', 'Costescu',
                             User.Role.INVENTORY, 'inventory', 'Stock Controller', 7000,
                             '+40 700 400 002', ago(180))

        return users

    # ──────────────────────────────────────────────────────────────
    # Customers
    # ──────────────────────────────────────────────────────────────

    def _customers(self):
        data = [
            ('Acme Corp SRL',         'contact@acmecorp.ro',         '+40 21 300 0001', 'Str. Victoriei 12, București'),
            ('Globex Industries SA',  'office@globex.ro',            '+40 21 300 0002', 'Calea Floreasca 55, București'),
            ('Initech Solutions SRL', 'sales@initech.ro',            '+40 21 300 0003', 'Bd. Unirii 10, București'),
            ('Umbrella Tech SA',      'procurement@umbrella.ro',     '+40 264 300 001', 'Str. Memorandumului 4, Cluj-Napoca'),
            ('Stark Industries SRL',  'orders@stark.ro',             '+40 232 300 001', 'Str. Ștefan cel Mare 22, Iași'),
            ('Wayne Enterprises SA',  'supply@wayne.ro',             '+40 251 300 001', 'Str. Unirii 8, Craiova'),
            ('Oscorp Romania SRL',    'office@oscorp.ro',            '+40 21 300 0007', 'Str. Dorobanților 3, București'),
            ('Nakatomi Trading SRL',  'nakatomi@trading.ro',         '+40 244 300 001', 'Bd. Republicii 15, Ploiești'),
            ('Cyberdyne Systems SA',  'info@cyberdyne.ro',           '+40 21 300 0009', 'Str. Buzești 4, București'),
            ('Rekall Corp SRL',       'rekall@corp.ro',              '+40 268 300 001', 'Str. Mureșenilor 7, Brașov'),
            ('Soylent Green SA',      'orders@soylent.ro',           '+40 21 300 0011', 'Calea Victoriei 88, București'),
            ('Yoyodyne SRL',          'yoyo@dyne.ro',                '+40 256 300 001', 'Str. Mihai Viteazul 1, Timișoara'),
        ]
        customers = []
        for name, email, phone, addr in data:
            customers.append(Customer.objects.create(
                name=name, contact_email=email, contact_phone=phone, address=addr,
            ))
        return customers

    # ──────────────────────────────────────────────────────────────
    # Products
    # ──────────────────────────────────────────────────────────────

    def _products(self):
        data = [
            # (name, sku, category, price_ron, stock, min_stock)
            ('Laptop ProBook 14"',     'LPT-001', 'SALES',     6800,  45, 10),
            ('Laptop UltraSlim 15"',   'LPT-002', 'SALES',     9200,  18, 5),
            ('Monitor 27" 4K',         'MNT-001', 'SALES',     3200,  30, 8),
            ('Mechanical Keyboard',    'KBD-001', 'SALES',      480,  60, 15),
            ('Wireless Mouse',         'MOU-001', 'SALES',      220, 120, 20),
            ('USB-C Hub 7-in-1',       'HUB-001', 'SALES',      350,  80, 20),
            ('Webcam HD 1080p',        'WBC-001', 'SALES',      620,  25, 8),
            ('Headset Noise Cancel',   'HDS-001', 'SALES',      890,  15, 5),
            ('Docking Station',        'DKS-001', 'SALES',     1450,  12, 5),
            ('External SSD 1TB',       'SSD-001', 'SALES',      760,  40, 10),
            ('Network Switch 24p',     'NSW-001', 'INVENTORY', 2800,   8, 3),
            ('Patch Cable Cat6 (box)', 'CBL-001', 'INVENTORY',  180,   4, 5),
            ('Server Rack Unit 2U',    'SRV-001', 'INVENTORY', 8400,   3, 2),
            ('UPS 1500VA',             'UPS-001', 'INVENTORY', 1200,   2, 3),
            ('Laser Printer A4',       'PRT-001', 'GENERAL',   1800,   0, 3),
        ]
        products = {}
        for name, sku, cat, price, stock, min_stock in data:
            p = Product.objects.create(
                name=name, sku=sku, category=cat,
                unit_price_ron=Decimal(str(price)),
                min_stock=min_stock,
            )
            # Set stock directly, bypassing save() auto-adjust
            Product.objects.filter(pk=p.pk).update(stock_count=stock)
            p.stock_count = stock
            products[sku] = p
        return products

    # ──────────────────────────────────────────────────────────────
    # Suppliers
    # ──────────────────────────────────────────────────────────────

    def _suppliers(self):
        data = [
            ('TechDistrib SRL',    'orders@techdistrib.ro',   '+40 21 500 0001'),
            ('PC Components SA',   'supply@pccomp.ro',        '+40 21 500 0002'),
            ('EuroTech Import SRL','import@eurotech.ro',      '+40 264 500 001'),
            ('ServerPro Romania',  'sales@serverpro.ro',      '+40 21 500 0004'),
            ('Electro Wholesale',  'wholesale@electro.ro',    '+40 256 500 001'),
        ]
        suppliers = []
        for name, email, phone in data:
            suppliers.append(Supplier.objects.create(
                name=name, contact_email=email, contact_phone=phone,
            ))
        return suppliers

    # ──────────────────────────────────────────────────────────────
    # Stock Movements (bypasses save() to avoid double-adjusting stock)
    # ──────────────────────────────────────────────────────────────

    def _stock_movements(self, products, suppliers, users):
        inv_user = users['inv1']
        sup0, sup1, sup2, sup3, sup4 = suppliers

        movements = [
            # INBOUND deliveries
            ('INBOUND',  'LPT-001', sup0, 50, ago(85)),
            ('INBOUND',  'LPT-002', sup0, 20, ago(80)),
            ('INBOUND',  'MNT-001', sup1, 35, ago(75)),
            ('INBOUND',  'KBD-001', sup1, 80, ago(70)),
            ('INBOUND',  'MOU-001', sup1, 150, ago(70)),
            ('INBOUND',  'HUB-001', sup2, 100, ago(65)),
            ('INBOUND',  'WBC-001', sup2, 30, ago(60)),
            ('INBOUND',  'HDS-001', sup0, 20, ago(55)),
            ('INBOUND',  'DKS-001', sup0, 15, ago(55)),
            ('INBOUND',  'SSD-001', sup1, 50, ago(50)),
            ('INBOUND',  'NSW-001', sup3, 10, ago(45)),
            ('INBOUND',  'CBL-001', sup4, 10, ago(45)),
            ('INBOUND',  'SRV-001', sup3, 5,  ago(40)),
            ('INBOUND',  'UPS-001', sup3, 5,  ago(40)),
            ('INBOUND',  'PRT-001', sup4, 5,  ago(35)),
            # OUTBOUND (sales fulfilment)
            ('OUTBOUND', 'LPT-001', None, 5,  ago(30)),
            ('OUTBOUND', 'MOU-001', None, 30, ago(28)),
            ('OUTBOUND', 'KBD-001', None, 20, ago(25)),
            ('OUTBOUND', 'SSD-001', None, 10, ago(20)),
            ('OUTBOUND', 'WBC-001', None, 5,  ago(15)),
            ('OUTBOUND', 'PRT-001', None, 5,  ago(10)),
            ('OUTBOUND', 'UPS-001', None, 3,  ago(8)),
            ('OUTBOUND', 'CBL-001', None, 6,  ago(5)),
            # WRITE_OFF
            ('WRITE_OFF', 'LPT-002', None, 2, ago(60)),
            # ADJUSTMENT (no stock change)
            ('ADJUSTMENT', 'MNT-001', None, 5, ago(20)),
        ]

        bulk = []
        for mtype, sku, supplier, qty, expected in movements:
            bulk.append(StockMovement(
                movement_type=mtype,
                product=products[sku],
                supplier=supplier,
                quantity=qty,
                expected_date=expected,
                created_by=inv_user,
            ))
        StockMovement.objects.bulk_create(bulk)

    # ──────────────────────────────────────────────────────────────
    # Orders & Order Items
    # ──────────────────────────────────────────────────────────────

    def _orders(self, customers, users, products):
        sales_users = [users['sales1'], users['sales2'], users['sales3'], users['sales4']]
        prods = list(products.values())

        # (customer_idx, sales_user_key, days_ago, status, channel, items)
        # items: list of (sku, qty, unit_price)
        raw = [
            (0,  'sales1', 88, 'DELIVERED', 'EMAG',    [('LPT-001',1,6800),('MOU-001',2,220)]),
            (1,  'sales1', 85, 'DELIVERED', 'WEBSITE', [('MNT-001',2,3200),('KBD-001',2,480)]),
            (2,  'sales2', 83, 'DELIVERED', 'DIRECT',  [('HUB-001',5,350),('WBC-001',2,620)]),
            (3,  'sales3', 80, 'DELIVERED', 'EMAG',    [('SSD-001',3,760),('MOU-001',3,220)]),
            (4,  'sales1', 78, 'DELIVERED', 'WEBSITE', [('LPT-002',1,9200)]),
            (5,  'sales2', 75, 'DELIVERED', 'DIRECT',  [('HDS-001',2,890),('DKS-001',1,1450)]),
            (6,  'sales3', 73, 'DELIVERED', 'EMAG',    [('KBD-001',4,480),('MOU-001',4,220)]),
            (7,  'sales4', 70, 'DELIVERED', 'WEBSITE', [('MNT-001',1,3200),('HUB-001',2,350)]),
            (8,  'sales1', 68, 'DELIVERED', 'EMAG',    [('LPT-001',2,6800)]),
            (9,  'sales2', 65, 'DELIVERED', 'DIRECT',  [('SSD-001',5,760),('WBC-001',2,620)]),
            (10, 'sales3', 63, 'DELIVERED', 'EMAG',    [('KBD-001',6,480)]),
            (11, 'sales1', 60, 'DELIVERED', 'WEBSITE', [('HDS-001',3,890)]),
            (0,  'sales2', 58, 'DELIVERED', 'EMAG',    [('LPT-001',1,6800),('DKS-001',1,1450)]),
            (1,  'sales3', 55, 'DELIVERED', 'DIRECT',  [('MNT-001',2,3200)]),
            (2,  'sales4', 53, 'DELIVERED', 'WEBSITE', [('HUB-001',10,350),('MOU-001',10,220)]),
            (3,  'sales1', 50, 'DELIVERED', 'EMAG',    [('SSD-001',4,760)]),
            (4,  'sales2', 48, 'SHIPPED',   'EMAG',    [('LPT-002',2,9200)]),
            (5,  'sales3', 45, 'DELIVERED', 'DIRECT',  [('WBC-001',3,620),('KBD-001',3,480)]),
            (6,  'sales1', 43, 'DELIVERED', 'WEBSITE', [('HDS-001',2,890),('MOU-001',5,220)]),
            (7,  'sales2', 40, 'DELIVERED', 'EMAG',    [('MNT-001',1,3200),('HUB-001',3,350)]),
            (8,  'sales3', 38, 'DELIVERED', 'DIRECT',  [('LPT-001',1,6800)]),
            (9,  'sales4', 35, 'SHIPPED',   'EMAG',    [('SSD-001',6,760)]),
            (10, 'sales1', 33, 'DELIVERED', 'WEBSITE', [('KBD-001',5,480),('MOU-001',8,220)]),
            (11, 'sales2', 30, 'SHIPPED',   'EMAG',    [('LPT-001',2,6800),('HDS-001',1,890)]),
            (0,  'sales3', 28, 'DELIVERED', 'DIRECT',  [('DKS-001',2,1450)]),
            (1,  'sales1', 25, 'SHIPPED',   'EMAG',    [('LPT-002',1,9200),('MOU-001',3,220)]),
            (2,  'sales2', 23, 'DELIVERED', 'WEBSITE', [('MNT-001',3,3200)]),
            (3,  'sales3', 21, 'SHIPPED',   'EMAG',    [('HUB-001',8,350),('WBC-001',2,620)]),
            (4,  'sales4', 19, 'PROCESSING','WEBSITE', [('SSD-001',3,760),('KBD-001',2,480)]),
            (5,  'sales1', 17, 'SHIPPED',   'EMAG',    [('LPT-001',1,6800),('HDS-001',2,890)]),
            (6,  'sales2', 15, 'PROCESSING','DIRECT',  [('MNT-001',2,3200),('DKS-001',1,1450)]),
            (7,  'sales3', 13, 'PROCESSING','EMAG',    [('LPT-002',1,9200)]),
            (8,  'sales1', 11, 'PROCESSING','WEBSITE', [('KBD-001',4,480),('MOU-001',6,220)]),
            (9,  'sales4', 10, 'PROCESSING','EMAG',    [('SSD-001',5,760)]),
            (10, 'sales2', 8,  'PENDING',   'DIRECT',  [('HUB-001',6,350),('WBC-001',2,620)]),
            (11, 'sales3', 7,  'PENDING',   'EMAG',    [('LPT-001',2,6800)]),
            (0,  'sales1', 5,  'PENDING',   'WEBSITE', [('HDS-001',3,890),('MOU-001',4,220)]),
            (1,  'sales2', 4,  'PENDING',   'EMAG',    [('MNT-001',1,3200),('KBD-001',3,480)]),
            (2,  'sales3', 3,  'PENDING',   'DIRECT',  [('LPT-002',2,9200)]),
            (3,  'sales4', 2,  'PENDING',   'EMAG',    [('SSD-001',4,760),('DKS-001',1,1450)]),
            (4,  'sales1', 1,  'PENDING',   'WEBSITE', [('HUB-001',5,350),('WBC-001',3,620)]),
        ]

        orders = []
        for c_idx, su_key, days, status, channel, items in raw:
            total = sum(qty * price for _, qty, price in items)
            order = Order.objects.create(
                customer=customers[c_idx],
                created_by=users[su_key],
                value_ron=Decimal(str(total)),
                date=ago(days),
                status=status,
                channel=channel,
            )
            OrderItem.objects.bulk_create([
                OrderItem(
                    order=order,
                    product=products[sku],
                    quantity=qty,
                    unit_price_ron=Decimal(str(price)),
                )
                for sku, qty, price in items
            ])
            orders.append(order)
        return orders

    # ──────────────────────────────────────────────────────────────
    # Invoices
    # ──────────────────────────────────────────────────────────────

    def _invoices(self, orders, users):
        sales_user = users['sales1']
        bulk = []
        for i, order in enumerate(orders, start=1):
            inv_no = f'INV-2026-{i:04d}'
            if order.status == 'DELIVERED':
                status = Invoice.Status.PAID
            elif order.status in ('SHIPPED', 'PROCESSING'):
                status = Invoice.Status.ISSUED
            else:
                status = Invoice.Status.DRAFT
            bulk.append(Invoice(
                invoice_number=inv_no,
                order=order,
                issued_by=sales_user,
                status=status,
                amount_ron=order.value_ron,
                issued_date=order.date,
                due_date=order.date + timedelta(days=30),
            ))
        Invoice.objects.bulk_create(bulk)

    # ──────────────────────────────────────────────────────────────
    # Attendance  (last 30 workdays for all employees)
    # ──────────────────────────────────────────────────────────────

    def _attendance(self, users):
        employees = list(users.values())
        # Status rotation per employee to make it realistic
        status_patterns = {
            'ceo':    ['PRESENT'] * 18 + ['REMOTE'] * 8 + ['ABSENT'] * 4,
            'hr1':    ['PRESENT'] * 20 + ['REMOTE'] * 6 + ['ABSENT'] * 2 + ['LEAVE'] * 2,
            'hr2':    ['PRESENT'] * 16 + ['REMOTE'] * 4 + ['ABSENT'] * 6 + ['LEAVE'] * 4,
            'it1':    ['PRESENT'] * 15 + ['REMOTE'] * 12 + ['ABSENT'] * 3,
            'it2':    ['PRESENT'] * 18 + ['REMOTE'] * 8 + ['ABSENT'] * 4,
            'it3':    ['PRESENT'] * 20 + ['REMOTE'] * 5 + ['ABSENT'] * 5,
            'sales1': ['PRESENT'] * 22 + ['REMOTE'] * 4 + ['ABSENT'] * 4,
            'sales2': ['PRESENT'] * 18 + ['REMOTE'] * 6 + ['ABSENT'] * 6,
            'sales3': ['PRESENT'] * 20 + ['REMOTE'] * 5 + ['ABSENT'] * 5,
            'sales4': ['PRESENT'] * 24 + ['ABSENT'] * 6,
            'inv1':   ['PRESENT'] * 22 + ['REMOTE'] * 4 + ['ABSENT'] * 4,
            'inv2':   ['PRESENT'] * 20 + ['REMOTE'] * 3 + ['ABSENT'] * 7,
        }
        days = list(workdays(ago(60), ago(1)))[-30:]  # last 30 workdays
        bulk = []
        for key, user in users.items():
            pattern = status_patterns.get(key, ['PRESENT'] * 25 + ['ABSENT'] * 5)
            for i, day in enumerate(days):
                status = pattern[i % len(pattern)]
                bulk.append(Attendance(employee=user, date=day, status=status))
        Attendance.objects.bulk_create(bulk, ignore_conflicts=True)

    # ──────────────────────────────────────────────────────────────
    # Leave Requests
    # ──────────────────────────────────────────────────────────────

    def _leave_requests(self, users, depts):
        ceo  = users['ceo']
        hr1  = users['hr1']
        data = [
            (users['hr2'],    depts['hr'],        'VACATION', ago(60), ago(55), 'APPROVED', hr1),
            (users['it3'],    depts['it'],         'SICK',     ago(30), ago(28), 'APPROVED', hr1),
            (users['sales2'], depts['sales'],      'VACATION', ago(45), ago(35), 'APPROVED', hr1),
            (users['sales4'], depts['sales'],      'VACATION', ago(10), ago(7),  'PENDING',  None),
            (users['inv2'],   depts['inventory'],  'SICK',     ago(5),  ago(3),  'APPROVED', hr1),
            (users['it2'],    depts['it'],         'UNPAID',   ago(90), ago(85), 'REJECTED', hr1),
            (users['sales3'], depts['sales'],      'VACATION', ago(2),  today_date := ago(0) + timedelta(days=5), 'PENDING', None),
            (users['hr2'],    depts['hr'],         'VACATION', ago(0) + timedelta(days=10),
                                                              ago(0) + timedelta(days=17), 'PENDING', None),
        ]
        for emp, dept, ltype, from_d, to_d, status, approved_by in data:
            LeaveRequest.objects.create(
                employee=emp, department=dept, type=ltype,
                from_date=from_d, to_date=to_d,
                status=status, approved_by=approved_by,
                reason='Planned leave request',
            )

    # ──────────────────────────────────────────────────────────────
    # Contracts
    # ──────────────────────────────────────────────────────────────

    def _contracts(self, users, depts):
        contract_map = [
            ('ceo',    None,           'EMPLOYMENT', ago(1825), None,          35000),
            ('hr1',    'hr',           'EMPLOYMENT', ago(730),  None,          12000),
            ('hr2',    'hr',           'EMPLOYMENT', ago(400),  None,          8500),
            ('it1',    'it',           'EMPLOYMENT', ago(900),  None,          14000),
            ('it2',    'it',           'EMPLOYMENT', ago(500),  None,          11000),
            ('it3',    'it',           'EMPLOYMENT', ago(200),  ago(0) + timedelta(days=165), 8000),
            ('sales1', 'sales',        'EMPLOYMENT', ago(800),  None,          10000),
            ('sales2', 'sales',        'EMPLOYMENT', ago(365),  None,          7500),
            ('sales3', 'sales',        'EMPLOYMENT', ago(300),  None,          7500),
            ('sales4', 'sales',        'CONTRACTOR', ago(90),   ago(0) + timedelta(days=275), 6000),
            ('inv1',   'inventory',    'EMPLOYMENT', ago(600),  None,          11000),
            ('inv2',   'inventory',    'EMPLOYMENT', ago(180),  None,          7000),
        ]
        for i, (key, dept_slug, ctype, start, end, salary) in enumerate(contract_map, start=1):
            Contract.objects.create(
                contract_number=f'CTR-2026-{i:04d}',
                employee=users[key],
                department=depts.get(dept_slug) if dept_slug else None,
                type=ctype,
                start_date=start,
                end_date=end,
                salary_ron=Decimal(str(salary)),
            )

    # ──────────────────────────────────────────────────────────────
    # Payroll (last 4 months)
    # ──────────────────────────────────────────────────────────────

    def _payroll(self, users):
        months = [date(2026, 1, 1), date(2026, 2, 1), date(2026, 3, 1), date(2026, 4, 1)]
        bulk = []
        for key, user in users.items():
            gross = float(user.salary_ron)
            net   = round(gross * 0.685, 2)  # ~31.5% tax
            for month in months:
                paid = month < date(2026, 4, 1)
                bulk.append(PayrollEntry(
                    employee=user,
                    month=month,
                    gross_salary_ron=Decimal(str(gross)),
                    net_salary_ron=Decimal(str(net)),
                    paid=paid,
                ))
        PayrollEntry.objects.bulk_create(bulk, ignore_conflicts=True)

    # ──────────────────────────────────────────────────────────────
    # Tickets & Comments
    # ──────────────────────────────────────────────────────────────

    def _tickets(self, users, depts):
        it_dept = depts['it']
        it1 = users['it1']
        it2 = users['it2']
        it3 = users['it3']

        specs = [
            # (title, priority, status, requested_by, assigned_to, days_created, days_resolved)
            ('VPN connection dropping intermittently',         'HIGH',   'RESOLVED',    users['sales1'], it1, 60, 57),
            ('Email client crashing on startup',               'MEDIUM', 'RESOLVED',    users['hr1'],    it2, 55, 52),
            ('Laptop keyboard not responding',                 'HIGH',   'RESOLVED',    users['sales2'], it1, 50, 47),
            ('Printer offline – Sales floor',                  'MEDIUM', 'RESOLVED',    users['sales3'], it3, 45, 43),
            ('Cannot access shared drive',                     'HIGH',   'RESOLVED',    users['hr2'],    it2, 42, 40),
            ('New employee laptop setup',                      'LOW',    'RESOLVED',    users['hr1'],    it3, 38, 35),
            ('Monitor flickering – Finance desk',              'MEDIUM', 'RESOLVED',    users['inv1'],   it1, 35, 33),
            ('Wi-Fi dead zone in Warehouse',                   'URGENT', 'RESOLVED',    users['inv2'],   it2, 30, 27),
            ('Software license expired – Adobe',               'MEDIUM', 'RESOLVED',    users['sales1'], it1, 28, 26),
            ('Backup job failing nightly',                     'URGENT', 'RESOLVED',    it2,             it1, 25, 22),
            ('CRM slow loading > 10 s',                        'HIGH',   'IN_PROGRESS', users['sales2'], it1, 20, None),
            ('Server room temperature alert',                  'URGENT', 'IN_PROGRESS', it1,             it2, 18, None),
            ('Antivirus false positive blocking app',          'MEDIUM', 'IN_PROGRESS', users['sales4'], it3, 15, None),
            ('Remote desktop cert expired',                    'HIGH',   'IN_PROGRESS', users['hr1'],    it2, 12, None),
            ('Cisco switch port blinking amber',               'HIGH',   'IN_PROGRESS', it2,             it1, 10, None),
            ('Employee onboarding – account provisioning',     'LOW',    'OPEN',        users['hr1'],    None, 8, None),
            ('Zoom audio issue on meeting room PC',            'MEDIUM', 'OPEN',        users['sales1'], None, 7, None),
            ('Two-factor auth not working on mobile',          'HIGH',   'OPEN',        users['sales3'], None, 6, None),
            ('Data export permission denied – BI tool',        'MEDIUM', 'OPEN',        users['inv1'],   None, 5, None),
            ('Keyboard shortcut broken after Windows update',  'LOW',    'OPEN',        users['hr2'],    None, 4, None),
            ('Request new monitor – Sales Team Lead',          'LOW',    'OPEN',        users['sales2'], None, 3, None),
            ('Password reset – forgot credentials',            'MEDIUM', 'OPEN',        users['inv2'],   None, 2, None),
            ('Slow internet on 3rd floor',                     'HIGH',   'OPEN',        users['sales4'], None, 1, None),
            ('USB-C dock not charging laptop',                 'MEDIUM', 'OPEN',        users['it3'],    None, 1, None),
            ('Request VPN access for remote work',             'LOW',    'OPEN',        users['hr2'],    None, 0, None),
        ]

        tickets = []
        for title, priority, status, requested_by, assigned_to, days_c, days_r in specs:
            created = dt(ago(days_c), hour=9)
            resolved_at = dt(ago(days_r), hour=16) if days_r is not None else None
            t = Ticket(
                title=title,
                description=f'User reported: {title.lower()}. Please investigate and resolve.',
                department=it_dept,
                priority=priority,
                status=status,
                requested_by=requested_by,
                assigned_to=assigned_to,
                resolved_at=resolved_at,
            )
            t.ticket_number = Ticket._generate_ticket_number()
            Ticket.objects.filter(pk__isnull=True)  # ensure sequence updated
            t.save()
            tickets.append(t)

        # Add comments on resolved/in-progress tickets
        comments = [
            (tickets[0],  it1, 'Identified the issue – DHCP lease renewal conflict. Applied fix.', ago(57)),
            (tickets[0],  users['sales1'], 'Working great now, thank you!', ago(57)),
            (tickets[7],  it2, 'Rerouted cable to access point 3. Signal now covers full warehouse.', ago(27)),
            (tickets[9],  it1, 'Cron job had wrong path after OS upgrade. Corrected and tested.', ago(22)),
            (tickets[10], it1, 'Profiling DB queries – found N+1 in customer list. Optimising.', ago(15)),
            (tickets[11], it2, 'Cooling unit fan replaced. Temperature back to 21°C.', ago(14)),
            (tickets[13], it2, 'New cert generated and deployed. Awaiting user confirmation.', ago(8)),
        ]
        TicketComment.objects.bulk_create([
            TicketComment(ticket=t, author=author, body=body, created_at=dt(d, hour=10))
            for t, author, body, d in comments
        ])

    # ──────────────────────────────────────────────────────────────
    # Notifications
    # ──────────────────────────────────────────────────────────────

    def _notifications(self, users):
        ceo    = users['ceo']
        hr1    = users['hr1']
        it1    = users['it1']
        sales1 = users['sales1']

        bulk = [
            Notification(recipient=ceo,    title='Q1 Revenue Target Achieved',
                         body='Sales hit 112% of Q1 target. Great work team!', is_read=True),
            Notification(recipient=ceo,    title='3 Leave Requests Pending Approval',
                         body='HR has flagged 3 leave requests requiring CEO sign-off.', is_read=False,
                         link='/reports'),
            Notification(recipient=hr1,    title='New Employee Contract Expiring',
                         body='Mihai Gheorghe contract expires in 165 days.', is_read=False),
            Notification(recipient=hr1,    title='Payroll for April Pending',
                         body='April payroll has not been marked as paid yet.', is_read=False),
            Notification(recipient=it1,    title='URGENT: Server Temperature Alert',
                         body='Server room temperature exceeded threshold. Ticket TKT-00012 opened.', is_read=False,
                         link='/it/tickets'),
            Notification(recipient=it1,    title='Backup Job Fixed',
                         body='Nightly backup is running successfully after last night\'s fix.', is_read=True),
            Notification(recipient=sales1, title='Large Order Received',
                         body='Acme Corp placed an order of 13,600 RON via eMAG.', is_read=True),
            Notification(recipient=sales1, title='Invoice INV-2026-0025 Overdue',
                         body='Payment for Rekall Corp invoice is overdue by 3 days.', is_read=False),
        ]
        Notification.objects.bulk_create(bulk)

    # ──────────────────────────────────────────────────────────────
    # Workflows
    # ──────────────────────────────────────────────────────────────

    def _workflows(self):
        workflows = [
            Workflow(
                name='Low Stock Alert',
                trigger_type='stock_below_min',
                trigger_config={'threshold': 'min_stock'},
                actions=[{'type': 'notify', 'recipients': ['INVENTORY', 'CEO']}],
                is_active=True,
            ),
            Workflow(
                name='New Order Notification',
                trigger_type='order_created',
                trigger_config={},
                actions=[{'type': 'notify', 'recipients': ['SALES']}],
                is_active=True,
            ),
            Workflow(
                name='Leave Request Auto-Approve (< 3 days)',
                trigger_type='leave_request_created',
                trigger_config={'max_days': 3},
                actions=[{'type': 'approve_leave'}, {'type': 'notify', 'recipients': ['HR']}],
                is_active=False,
            ),
            Workflow(
                name='Ticket SLA Breach Alert',
                trigger_type='ticket_sla_breach',
                trigger_config={'priority': 'HIGH', 'hours': 24},
                actions=[{'type': 'notify', 'recipients': ['IT', 'CEO']}],
                is_active=True,
            ),
        ]
        Workflow.objects.bulk_create(workflows)
        wf = Workflow.objects.first()
        WorkflowLog.objects.bulk_create([
            WorkflowLog(workflow=wf, trigger_input={'product': 'CBL-001', 'stock': 4},
                        trigger_result={'notified': True}),
            WorkflowLog(workflow=wf, trigger_input={'product': 'UPS-001', 'stock': 2},
                        trigger_result={'notified': True}),
        ])

    # ──────────────────────────────────────────────────────────────
    # Reports
    # ──────────────────────────────────────────────────────────────

    def _reports(self):
        data = [
            ('Monthly Revenue Report',    'monthly-revenue',       'Sales',     'Feb 2026', 142, date(2026, 3, 1)),
            ('Quarterly Profit & Loss',   'quarterly-pl',          'Finance',   'Q3 FY26',  318, date(2026, 3, 1)),
            ('Inventory Stock Report',    'inventory-stock',       'Inventory', 'Feb 2026',  95, date(2026, 3, 1)),
            ('HR Headcount Summary',      'hr-headcount',          'HR',        'Feb 2026',  78, date(2026, 3, 1)),
            ('IT Ticket SLA Report',      'it-ticket-sla',         'IT',        'Feb 2026',  56, date(2026, 3, 1)),
            ('Sales Channel Analysis',    'sales-channel-analysis','Sales',     'Q3 FY26',  204, date(2026, 2, 28)),
            ('Employee Attendance Report','employee-attendance',   'HR',        'Feb 2026', 112, date(2026, 2, 28)),
            ('Top Customers Report',      'top-customers',         'Sales',     'Q3 FY26',   88, date(2026, 2, 25)),
            ('Annual Tax Summary',        'annual-tax-summary',    'Finance',   'FY25',     1200, date(2026, 2, 15)),
        ]
        Report.objects.bulk_create([
            Report(
                name=name, slug=slug, category=cat,
                period=period, file_size_kb=size,
                generated_at=datetime(d.year, d.month, d.day, tzinfo=tz.utc),
            )
            for name, slug, cat, period, size, d in data
        ])
