"""
Comprehensive database seeder — covers every model with realistic demo data
spanning January 1 → June 30, 2026 (with current date anchored at 2026-05-19).

Run: python manage.py seed_db
"""
import random
from datetime import date, timedelta, datetime, timezone as tz
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from api.models import (
    Asset, Attendance, Contract, Customer, Department, Invoice,
    LeaveRequest, Notification, Order, OrderItem, PayrollEntry,
    Product, Report, StockMovement, Supplier, SystemStatus,
    Ticket, TicketComment, User, Workflow, WorkflowLog,
)

# Real wall-clock "today" the dashboards will use (see CLAUDE.md).
TODAY = date(2026, 5, 19)
WINDOW_START = date(2026, 1, 1)
WINDOW_END = date(2026, 6, 30)


def days_ago(n: int) -> date:
    return TODAY - timedelta(days=n)


def dt(d: date, hour: int = 9, minute: int = 0) -> datetime:
    return datetime(d.year, d.month, d.day, hour, minute, tzinfo=tz.utc)


def workdays(start: date, end: date):
    """Yield every weekday between start and end inclusive."""
    cur = start
    while cur <= end:
        if cur.weekday() < 5:
            yield cur
        cur += timedelta(days=1)


class Command(BaseCommand):
    help = 'Seed the database with comprehensive demo data (Jan–Jun 2026)'

    @transaction.atomic
    def handle(self, *args, **options):
        self.rng = random.Random(42)

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

        self.stdout.write('Assets…')
        self._assets(users)

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

        self.stdout.write('System status…')
        self._system_status()

        self.stdout.write('Notifications…')
        self._notifications(users)

        self.stdout.write('Workflows…')
        self._workflows()

        self.stdout.write('Reports…')
        self._reports()

        self.stdout.write(self.style.SUCCESS('✓ Database seeded (Jan–Jun 2026)'))

    # ──────────────────────────────────────────────────────────────
    # Clear
    # ──────────────────────────────────────────────────────────────

    def _clear(self):
        WorkflowLog.objects.all().delete()
        Workflow.objects.all().delete()
        Notification.objects.all().delete()
        TicketComment.objects.all().delete()
        Ticket.objects.all().delete()
        SystemStatus.objects.all().delete()
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
        Asset.objects.all().delete()
        User.objects.all().delete()
        Department.objects.all().delete()

    # ──────────────────────────────────────────────────────────────
    # Departments
    # ──────────────────────────────────────────────────────────────

    def _departments(self):
        specs = [
            ('Information Technology', 'it',         'Monitor'),
            ('Human Resources',        'hr',         'Users'),
            ('Sales',                  'sales',      'BarChart3'),
            ('Inventory',              'inventory',  'Package'),
            ('Finance',                'finance',    'Building2'),
        ]
        return {slug: Department.objects.create(name=name, slug=slug, icon=icon)
                for name, slug, icon in specs}

    # ──────────────────────────────────────────────────────────────
    # Users
    # ──────────────────────────────────────────────────────────────

    def _users(self, depts):
        def make(username, email, first, last, role, dept_slug, position,
                 salary, phone, start, emp_type=User.EmploymentType.FULL_TIME,
                 is_staff=False, is_superuser=False):
            return User.objects.create_user(
                username=username, email=email, password='password123',
                first_name=first, last_name=last, role=role,
                department=depts.get(dept_slug) if dept_slug else None,
                position=position, salary_ron=Decimal(str(salary)),
                phone=phone, start_date=start, employment_type=emp_type,
                is_staff=is_staff, is_superuser=is_superuser,
            )

        u = {}
        u['ceo']    = make('admin', 'admin@miez.ro', 'Andrei', 'Constantin',
                           User.Role.CEO, None, 'Chief Executive Officer',
                           35000, '+40 700 000 001', date(2021, 5, 1),
                           is_staff=True, is_superuser=True)

        # HR
        u['hr1']    = make('maria_pop', 'maria.pop@miez.ro', 'Maria', 'Pop',
                           User.Role.HR, 'hr', 'HR Manager',
                           12000, '+40 700 100 001', date(2024, 5, 19))
        u['hr2']    = make('ana_ionescu', 'ana.ionescu@miez.ro', 'Ana', 'Ionescu',
                           User.Role.HR, 'hr', 'HR Specialist',
                           8500, '+40 700 100 002', date(2025, 4, 14))
        u['hr3']    = make('diana_iliescu', 'diana.iliescu@miez.ro', 'Diana', 'Iliescu',
                           User.Role.HR, 'hr', 'Payroll Officer',
                           7800, '+40 700 100 003', date(2026, 2, 10))

        # IT
        u['it1']    = make('alex_stan', 'alex.stan@miez.ro', 'Alexandru', 'Stan',
                           User.Role.IT, 'it', 'IT Lead',
                           14000, '+40 700 200 001', date(2023, 12, 1))
        u['it2']    = make('dan_radu', 'dan.radu@miez.ro', 'Dan', 'Radu',
                           User.Role.IT, 'it', 'Systems Administrator',
                           11000, '+40 700 200 002', date(2025, 1, 6))
        u['it3']    = make('mihai_gheorghe', 'mihai.gheorghe@miez.ro', 'Mihai', 'Gheorghe',
                           User.Role.IT, 'it', 'IT Support Technician',
                           8000, '+40 700 200 003', date(2025, 11, 4))
        u['it4']    = make('vlad_dinescu', 'vlad.dinescu@miez.ro', 'Vlad', 'Dinescu',
                           User.Role.IT, 'it', 'Network Engineer',
                           10500, '+40 700 200 004', date(2026, 3, 16),
                           emp_type=User.EmploymentType.CONTRACTOR)

        # Sales
        u['sales1'] = make('elena_munteanu', 'elena.munteanu@miez.ro', 'Elena', 'Munteanu',
                           User.Role.SALES, 'sales', 'Senior Sales Representative',
                           10000, '+40 700 300 001', date(2024, 3, 11))
        u['sales2'] = make('bogdan_popa', 'bogdan.popa@miez.ro', 'Bogdan', 'Popa',
                           User.Role.SALES, 'sales', 'Sales Representative',
                           7500, '+40 700 300 002', date(2025, 5, 19))
        u['sales3'] = make('cristina_moldovan', 'cristina.moldovan@miez.ro', 'Cristina', 'Moldovan',
                           User.Role.SALES, 'sales', 'Sales Representative',
                           7500, '+40 700 300 003', date(2025, 7, 23))
        u['sales4'] = make('andrei_stoica', 'andrei.stoica@miez.ro', 'Andrei', 'Stoica',
                           User.Role.SALES, 'sales', 'Junior Sales Representative',
                           6000, '+40 700 300 004', date(2026, 2, 18))
        u['sales5'] = make('lavinia_serban', 'lavinia.serban@miez.ro', 'Lavinia', 'Șerban',
                           User.Role.SALES, 'sales', 'Sales Representative',
                           7500, '+40 700 300 005', date(2026, 5, 4),
                           emp_type=User.EmploymentType.PART_TIME)

        # Inventory
        u['inv1']   = make('ioana_dumitrescu', 'ioana.dumitrescu@miez.ro', 'Ioana', 'Dumitrescu',
                           User.Role.INVENTORY, 'inventory', 'Inventory Manager',
                           11000, '+40 700 400 001', date(2024, 9, 26))
        u['inv2']   = make('radu_costescu', 'radu.costescu@miez.ro', 'Radu', 'Costescu',
                           User.Role.INVENTORY, 'inventory', 'Stock Controller',
                           7000, '+40 700 400 002', date(2025, 11, 20))
        u['inv3']   = make('paul_voicu', 'paul.voicu@miez.ro', 'Paul', 'Voicu',
                           User.Role.INVENTORY, 'inventory', 'Warehouse Operator',
                           6200, '+40 700 400 003', date(2026, 5, 11))

        return u

    # ──────────────────────────────────────────────────────────────
    # Customers
    # ──────────────────────────────────────────────────────────────

    def _customers(self):
        Tier = Customer.Tier
        specs = [
            ('Acme Corp SRL',         'contact@acmecorp.ro',     '+40 21 300 0001', 'Str. Victoriei 12, București',         'București',     Tier.GOLD),
            ('Globex Industries SA',  'office@globex.ro',        '+40 21 300 0002', 'Calea Floreasca 55, București',        'București',     Tier.GOLD),
            ('Initech Solutions SRL', 'sales@initech.ro',        '+40 21 300 0003', 'Bd. Unirii 10, București',             'București',     Tier.SILVER),
            ('Umbrella Tech SA',      'procurement@umbrella.ro', '+40 264 300 001', 'Str. Memorandumului 4, Cluj-Napoca',   'Cluj-Napoca',    Tier.GOLD),
            ('Stark Industries SRL',  'orders@stark.ro',         '+40 232 300 001', 'Str. Ștefan cel Mare 22, Iași',        'Iași',           Tier.SILVER),
            ('Wayne Enterprises SA',  'supply@wayne.ro',         '+40 251 300 001', 'Str. Unirii 8, Craiova',               'Craiova',        Tier.GOLD),
            ('Oscorp Romania SRL',    'office@oscorp.ro',        '+40 21 300 0007', 'Str. Dorobanților 3, București',       'București',     Tier.SILVER),
            ('Nakatomi Trading SRL',  'nakatomi@trading.ro',     '+40 244 300 001', 'Bd. Republicii 15, Ploiești',          'Ploiești',       Tier.BRONZE),
            ('Cyberdyne Systems SA',  'info@cyberdyne.ro',       '+40 21 300 0009', 'Str. Buzești 4, București',            'București',     Tier.SILVER),
            ('Rekall Corp SRL',       'rekall@corp.ro',          '+40 268 300 001', 'Str. Mureșenilor 7, Brașov',           'Brașov',         Tier.BRONZE),
            ('Soylent Green SA',      'orders@soylent.ro',       '+40 21 300 0011', 'Calea Victoriei 88, București',        'București',     Tier.SILVER),
            ('Yoyodyne SRL',          'yoyo@dyne.ro',            '+40 256 300 001', 'Str. Mihai Viteazul 1, Timișoara',     'Timișoara',      Tier.BRONZE),
            ('Tyrell Corp SA',        'sales@tyrell.ro',         '+40 21 300 0013', 'Bd. Iuliu Maniu 25, București',        'București',     Tier.GOLD),
            ('Massive Dynamic SRL',   'orders@massive.ro',       '+40 264 300 002', 'Str. Eroilor 18, Cluj-Napoca',         'Cluj-Napoca',    Tier.SILVER),
            ('Pied Piper Tech SRL',   'hello@piedpiper.ro',      '+40 21 300 0015', 'Str. Lipscani 22, București',          'București',     Tier.BRONZE),
            ('Vandelay Imports SA',   'imports@vandelay.ro',     '+40 21 300 0016', 'Calea Călărașilor 4, București',       'București',     Tier.SILVER),
            ('Hooli Cloud SRL',       'b2b@hooli.ro',            '+40 256 300 002', 'Str. Eugeniu de Savoya 9, Timișoara',  'Timișoara',      Tier.GOLD),
            ('Maria Popescu',         'maria.p@gmail.com',       '+40 723 100 200', 'Str. Aviatorilor 11, Cluj-Napoca',     'Cluj-Napoca',    Tier.INDIVIDUAL),
        ]
        customers = []
        for name, email, phone, addr, location, tier in specs:
            customers.append(Customer.objects.create(
                name=name, contact_email=email, contact_phone=phone,
                address=addr, location=location, tier=tier,
            ))
        return customers


    def _assets(self, users):
        specs = [
            ('Alex Lead Laptop', 'ASSET-LAP-001', 'LAPTOP', users['it1'], 'ASSIGNED', 'Primary IT lead workstation.'),
            ('Dan Support Laptop', 'ASSET-LAP-002', 'LAPTOP', users['it2'], 'ASSIGNED', 'Issued to systems administrator.'),
            ('CEO Travel Laptop', 'ASSET-LAP-004', 'LAPTOP', users['ceo'], 'ASSIGNED', 'Lightweight laptop for executive travel.'),
            ('HR Onboarding Laptop', 'ASSET-LAP-005', 'LAPTOP', users['hr2'], 'ASSIGNED', 'Used for HR onboarding sessions.'),
            ('Spare Dell Monitor', 'ASSET-MON-001', 'MONITOR', None, 'AVAILABLE', 'Backup monitor stored in IT cabinet.'),
            ('Sales Demo Monitor', 'ASSET-MON-003', 'MONITOR', users['sales1'], 'ASSIGNED', 'Portable monitor for client demos.'),
            ('Reception Phone', 'ASSET-PHN-001', 'PHONE', users['hr1'], 'ASSIGNED', 'Reception desk handset.'),
            ('CEO Mobile Phone', 'ASSET-PHN-002', 'PHONE', users['ceo'], 'ASSIGNED', 'Executive mobile device with MDM enrolled.'),
            ('Docking Station', 'ASSET-PER-001', 'PERIPHERAL', users['it3'], 'ASSIGNED', 'USB-C dock for IT support.'),
            ('Warehouse Barcode Scanner', 'ASSET-PER-003', 'PERIPHERAL', users['inv2'], 'ASSIGNED', 'Handheld scanner for stock checks.'),
            ('Conference Webcam', 'ASSET-PER-004', 'PERIPHERAL', None, 'MAINTENANCE', 'Needs firmware update before next meeting room install.'),
            ('Retired Lenovo Laptop', 'ASSET-LAP-003', 'LAPTOP', None, 'RETIRED', 'Old laptop removed from circulation.'),
            ('Conference Room Display', 'ASSET-MON-002', 'MONITOR', users['ceo'], 'MAINTENANCE', 'Awaiting HDMI controller repair.'),
            ('Wireless Mouse Kit', 'ASSET-PER-002', 'PERIPHERAL', None, 'AVAILABLE', 'Spare peripherals for new hires.'),
            ('Spare Office Tablet', 'ASSET-TBL-001', 'OTHER', None, 'AVAILABLE', 'Shared tablet for presentations and approvals.'),
        ]

        for name, serial, category, assigned_to, status, notes in specs:
            Asset.objects.create(
                name=name,
                serial_number=serial,
                category=category,
                assigned_to=assigned_to,
                status=status,
                notes=notes,
            )

    # ──────────────────────────────────────────────────────────────
    # Products  (final stock_count is set independently of movements)
    # ──────────────────────────────────────────────────────────────

    def _products(self):
        # (name, sku, category, unit_price_ron, final_stock, min_stock)
        specs = [
            # Electronics – sales-driven
            ('Laptop ProBook 14"',     'LPT-001', 'SALES',     6800,  42, 10),
            ('Laptop UltraSlim 15"',   'LPT-002', 'SALES',     9200,  16, 5),
            ('Laptop Gaming 17"',      'LPT-003', 'SALES',    11500,   7, 5),
            ('Monitor 27" 4K',         'MNT-001', 'SALES',     3200,  28, 8),
            ('Monitor 32" Ultrawide',  'MNT-002', 'SALES',     4900,  14, 5),
            ('Monitor 24" FHD',        'MNT-003', 'SALES',     1200,  55, 12),
            ('Mechanical Keyboard',    'KBD-001', 'SALES',      480,  64, 15),
            ('Wireless Mouse',         'MOU-001', 'SALES',      220, 132, 20),
            ('USB-C Hub 7-in-1',       'HUB-001', 'SALES',      350,  86, 20),
            ('Webcam HD 1080p',        'WBC-001', 'SALES',      620,  21, 8),
            ('Webcam 4K Studio',       'WBC-002', 'SALES',     1450,   9, 5),
            ('Headset Noise Cancel',   'HDS-001', 'SALES',      890,  12, 5),
            ('Docking Station',        'DKS-001', 'SALES',     1450,  18, 5),
            ('External SSD 1TB',       'SSD-001', 'SALES',      760,  36, 10),
            ('External SSD 2TB',       'SSD-002', 'SALES',     1380,  11, 5),
            ('Tablet 11" 128GB',       'TBL-001', 'SALES',     3400,  17, 6),

            # Infrastructure – low rotation
            ('Network Switch 24p',     'NSW-001', 'INVENTORY', 2800,   6, 3),
            ('Patch Cable Cat6 (box)', 'CBL-001', 'INVENTORY',  180,   4, 5),    # low stock
            ('Server Rack Unit 2U',    'SRV-001', 'INVENTORY', 8400,   2, 2),    # low stock
            ('UPS 1500VA',             'UPS-001', 'INVENTORY', 1200,   2, 3),    # low stock
            ('Wireless Access Point',  'WAP-001', 'INVENTORY',  640,  18, 6),

            # Out-of-stock
            ('Laser Printer A4',       'PRT-001', 'GENERAL',   1800,   0, 3),
            ('Projector 4K',           'PRJ-001', 'GENERAL',   5200,   0, 2),
        ]
        products = {}
        for name, sku, cat, price, stock, min_stock in specs:
            p = Product.objects.create(
                name=name, sku=sku, category=cat,
                unit_price_ron=Decimal(str(price)), min_stock=min_stock,
            )
            Product.objects.filter(pk=p.pk).update(stock_count=stock)
            p.stock_count = stock
            products[sku] = p
        return products

    # ──────────────────────────────────────────────────────────────
    # Suppliers
    # ──────────────────────────────────────────────────────────────

    def _suppliers(self):
        specs = [
            ('TechDistrib SRL',     'orders@techdistrib.ro',  '+40 21 500 0001'),
            ('PC Components SA',    'supply@pccomp.ro',       '+40 21 500 0002'),
            ('EuroTech Import SRL', 'import@eurotech.ro',     '+40 264 500 001'),
            ('ServerPro Romania',   'sales@serverpro.ro',     '+40 21 500 0004'),
            ('Electro Wholesale',   'wholesale@electro.ro',   '+40 256 500 001'),
            ('Asia Direct Logistics','logistics@asiadirect.ro','+40 21 500 0006'),
            ('NordicTech Bucharest','nordic@bucharest.ro',    '+40 21 500 0007'),
        ]
        return [Supplier.objects.create(name=n, contact_email=e, contact_phone=p)
                for n, e, p in specs]

    # ──────────────────────────────────────────────────────────────
    # Stock Movements
    # Created via bulk_create (bypasses save() auto-adjust) so the
    # final product stock_count we set in _products() is authoritative.
    # created_at is then backdated via .update() so the 7-day Sankey
    # has dense recent activity.
    # ──────────────────────────────────────────────────────────────

    def _stock_movements(self, products, suppliers, users):
        inv_user = users['inv1']
        sup = suppliers
        skus = list(products.keys())

        # Ancorăm calculele dinamice la data curentă (1 Iunie 2026)
        REAL_TODAY = date(2026, 6, 1)

        # 1. Istoric masiv din lunile trecute (Ianuarie – Mai)
        history = [
            ('INBOUND', 'LPT-001', sup[0], 50, date(2026, 1, 12), date(2026, 1, 15)),
            ('INBOUND', 'LPT-002', sup[0], 20, date(2026, 1, 14), date(2026, 1, 17)),
            ('INBOUND', 'MOU-001', sup[1], 150, date(2026, 1, 20), date(2026, 1, 22)),
            ('INBOUND', 'KBD-001', sup[1], 80, date(2026, 1, 25), date(2026, 1, 27)),
            ('INBOUND', 'MNT-001', sup[1], 35, date(2026, 2, 3), date(2026, 2, 5)),
            ('INBOUND', 'HUB-001', sup[2], 120, date(2026, 2, 10), date(2026, 2, 12)),
            ('INBOUND', 'WBC-001', sup[2], 40, date(2026, 2, 15), date(2026, 2, 17)),
            ('INBOUND', 'SSD-001', sup[1], 60, date(2026, 2, 22), date(2026, 2, 24)),
            ('INBOUND', 'HDS-001', sup[0], 30, date(2026, 3, 2), date(2026, 3, 5)),
            ('INBOUND', 'LPT-003', sup[5], 12, date(2026, 3, 14), date(2026, 3, 18)),
            ('INBOUND', 'MNT-003', sup[1], 70, date(2026, 4, 26), date(2026, 4, 28)),
            ('INBOUND', 'MOU-001', sup[6], 60, date(2026, 5, 1), date(2026, 5, 4)),
            ('INBOUND', 'KBD-001', sup[6], 40, date(2026, 5, 15), date(2026, 5, 18)),
            ('OUTBOUND',   'LPT-001', None, 8, date(2026, 2, 28), date(2026, 2, 28)),
            ('OUTBOUND',   'MOU-001', None, 20, date(2026, 3, 6), date(2026, 3, 6)),
            ('WRITE_OFF',  'LPT-002', None, 2, date(2026, 4, 11), date(2026, 4, 11)),
            ('ADJUSTMENT', 'MNT-001', None, 28, date(2026, 5, 10), date(2026, 5, 10)),
        ]

        # 2. Date ULTRA-RECENTE (Ultimele zile din Mai și AZI, 1 Iunie)
        recent = [
            ('INBOUND',  'LPT-001', sup[0], 15, REAL_TODAY - timedelta(days=4), REAL_TODAY - timedelta(days=2)),
            ('INBOUND',  'MNT-001', sup[1], 10, REAL_TODAY - timedelta(days=3), REAL_TODAY - timedelta(days=1)),
            ('INBOUND',  'KBD-001', sup[2], 25, REAL_TODAY - timedelta(days=2), REAL_TODAY - timedelta(days=1)),
            ('INBOUND',  'MOU-001', sup[6], 50, REAL_TODAY - timedelta(days=1), REAL_TODAY),
            
            # LIVRĂRI COPTUȘITE AZI (Apar pe dashboard ca "Deliveries Today" - 1 Iunie)
            ('INBOUND',  'LPT-003', sup[5], 8,  REAL_TODAY - timedelta(days=1), REAL_TODAY),
            ('INBOUND',  'DKS-001', sup[0], 12, REAL_TODAY - timedelta(days=2), REAL_TODAY),
            
            # Flux de ieșiri (Outbound/Write-Off) de ieri/azi
            ('OUTBOUND', 'LPT-001', None, 4, REAL_TODAY - timedelta(days=1), REAL_TODAY - timedelta(days=1)),
            ('OUTBOUND', 'MOU-001', None, 15, REAL_TODAY, REAL_TODAY),
            ('WRITE_OFF', 'MNT-003', None, 2, REAL_TODAY - timedelta(days=2), REAL_TODAY - timedelta(days=2)),
        ]

        # 3. VIITORUL APROPIAT (Următoarele zile + FIX PESTE 3 ZILE: 4 Iunie 2026)
        future = [
            ('INBOUND',  'MNT-002', sup[1], 7,  REAL_TODAY, REAL_TODAY + timedelta(days=1)), # Mâine (2 Iunie)
            ('INBOUND',  'SSD-001', sup[4], 30, REAL_TODAY, REAL_TODAY + timedelta(days=2)), # Peste 2 zile (3 Iunie)
            
            # ────────────────────────────────────────────────────────
            # !!! LIVRĂRI PROGRAMATE EXACT PESTE 3 ZILE (4 IUNIE 2026) !!!
            # ────────────────────────────────────────────────────────
            ('INBOUND',  'PRT-001', sup[3], 15, REAL_TODAY, REAL_TODAY + timedelta(days=3)), 
            ('INBOUND',  'UPS-001', sup[4], 5,  REAL_TODAY, REAL_TODAY + timedelta(days=3)), 
            ('INBOUND',  'HUB-001', sup[0], 40, REAL_TODAY, REAL_TODAY + timedelta(days=3)),
            
            # Livrări mai îndepărtate în Iunie
            ('INBOUND',  'PRJ-001', sup[6], 4,  REAL_TODAY, REAL_TODAY + timedelta(days=10)),
            ('INBOUND',  'SRV-001', sup[3], 2,  REAL_TODAY, REAL_TODAY + timedelta(days=14)),
        ]

        all_specs = history + recent + future

        # Creare în masă
        StockMovement.objects.bulk_create([
            StockMovement(
                movement_type=mtype,
                product=products[sku],
                supplier=supplier,
                quantity=qty,
                expected_date=expected,
                created_by=inv_user,
            )
            for mtype, sku, supplier, qty, _created, expected in all_specs
        ])

        # Sincronizare timestamps 'created_at' în DB pentru realism istoric
        for mtype, sku, supplier, qty, created, _expected in all_specs:
            qs = StockMovement.objects.filter(
                movement_type=mtype, product=products[sku], quantity=qty,
            )
            if supplier is not None:
                qs = qs.filter(supplier=supplier)
            
            row = qs.filter(created_at__date__gt=date(2026, 1, 1) - timedelta(days=1)).order_by('id').first()
            if row and row.created_at.date() != created:
                StockMovement.objects.filter(pk=row.pk).update(
                    created_at=dt(created, hour=10)
                )

    # ──────────────────────────────────────────────────────────────
    # Orders & Order Items
    # ──────────────────────────────────────────────────────────────

    def _orders(self, customers, users, products):
        rng = self.rng
        sales_keys = ['sales1', 'sales2', 'sales3', 'sales4', 'sales5']
        channels = ['EMAG', 'WEBSITE', 'DIRECT']
        sku_pool = list(products.keys())

        # (start, end, n_orders) – distribution shaping the trend
        monthly_plan = [
            (date(2026, 1, 2),  date(2026, 1, 31), 14),
            (date(2026, 2, 1),  date(2026, 2, 28), 18),
            (date(2026, 3, 1),  date(2026, 3, 31), 22),
            (date(2026, 4, 1),  date(2026, 4, 30), 26),
            (date(2026, 5, 1),  date(2026, 5, 17), 22),
            # Last 7 days (heavy density for daily-orders / revenue-trend charts)
            (days_ago(6),       TODAY,              18),
            # Future PENDING / PROCESSING pipeline (visible on orders page)
            (TODAY + timedelta(days=1), date(2026, 6, 20), 12),
        ]

        # sales5 only employed since 2026-05-04
        sales5_eligible_from = date(2026, 5, 4)

        orders = []
        for start, end, count in monthly_plan:
            span = max((end - start).days, 0)
            for _ in range(count):
                day = start + timedelta(days=rng.randint(0, span))
                customer = customers[rng.randint(0, len(customers) - 1)]
                # pick a sales user, but exclude sales5 before their start date
                eligible = [k for k in sales_keys
                            if k != 'sales5' or day >= sales5_eligible_from]
                # also exclude sales4 before their start (2026-02-18)
                eligible = [k for k in eligible
                            if k != 'sales4' or day >= date(2026, 2, 18)]
                sales_key = rng.choice(eligible)
                channel = rng.choice(channels)

                # 1–4 line items, no repeats
                n_items = rng.randint(1, 4)
                chosen = rng.sample(sku_pool, k=min(n_items, len(sku_pool)))
                items = []
                for sku in chosen:
                    prod = products[sku]
                    # Heavier ticket items in smaller quantities
                    if sku.startswith(('LPT', 'MNT', 'PRJ', 'SRV', 'NSW')):
                        qty = rng.randint(1, 3)
                    elif sku.startswith(('TBL', 'DKS', 'HDS', 'UPS')):
                        qty = rng.randint(1, 4)
                    else:
                        qty = rng.randint(1, 8)
                    items.append((sku, qty, float(prod.unit_price_ron)))

                # Status by age (negative age = future order)
                age = (TODAY - day).days
                if age < 0:
                    status = rng.choice(['PENDING', 'PENDING', 'PROCESSING'])
                elif age <= 1:
                    status = rng.choice(['PENDING', 'PROCESSING'])
                elif age <= 4:
                    status = rng.choice(['PROCESSING', 'SHIPPED'])
                elif age <= 10:
                    status = rng.choice(['SHIPPED', 'DELIVERED', 'DELIVERED'])
                elif age <= 90:
                    # occasional returned to make the metric non-zero
                    status = rng.choices(
                        ['DELIVERED', 'DELIVERED', 'DELIVERED', 'RETURNED'],
                        weights=[80, 10, 8, 2], k=1,
                    )[0]
                else:
                    status = 'DELIVERED'

                total = sum(qty * price for _, qty, price in items)
                order = Order.objects.create(
                    customer=customer,
                    created_by=users[sales_key],
                    value_ron=Decimal(str(total)),
                    date=day,
                    status=status,
                    channel=channel,
                )
                OrderItem.objects.bulk_create([
                    OrderItem(order=order, product=products[sku],
                              quantity=qty, unit_price_ron=Decimal(str(price)))
                    for sku, qty, price in items
                ])
                orders.append(order)

        # Guarantee at least one DELIVERED order yesterday (drives revenue %-change KPI)
        anchor_yesterday = days_ago(1)
        if not any(o.date == anchor_yesterday and o.status == 'DELIVERED' for o in orders):
            order = Order.objects.create(
                customer=customers[0], created_by=users['sales1'],
                value_ron=Decimal('13600.00'), date=anchor_yesterday,
                status='DELIVERED', channel='EMAG',
            )
            OrderItem.objects.create(
                order=order, product=products['LPT-001'],
                quantity=2, unit_price_ron=Decimal('6800.00'),
            )
            orders.append(order)

        return orders

    # ──────────────────────────────────────────────────────────────
    # Invoices  (1 per order, with sensible status + due dates)
    # ──────────────────────────────────────────────────────────────

    def _invoices(self, orders, users):
        sales_user = users['sales1']
        bulk = []
        for i, order in enumerate(orders, start=1):
            inv_no = f'INV-2026-{i:04d}'
            due = order.date + timedelta(days=30)
            if order.status == 'DELIVERED':
                # ~10% of delivered orders past due-date end up overdue (ISSUED unpaid)
                if due < TODAY and self.rng.random() < 0.08:
                    status = Invoice.Status.ISSUED  # overdue (unpaid)
                else:
                    status = Invoice.Status.PAID
            elif order.status in ('SHIPPED', 'PROCESSING'):
                status = Invoice.Status.ISSUED
            elif order.status == 'RETURNED':
                status = Invoice.Status.CANCELLED
            else:
                status = Invoice.Status.DRAFT
            bulk.append(Invoice(
                invoice_number=inv_no, order=order, issued_by=sales_user,
                status=status, amount_ron=order.value_ron,
                issued_date=order.date, due_date=due,
            ))
        Invoice.objects.bulk_create(bulk)

    # ──────────────────────────────────────────────────────────────
    # Attendance  (every workday Jan 5 → yesterday, all employees)
    # ──────────────────────────────────────────────────────────────

    def _attendance(self, users):
        rng = self.rng
        # Per-employee mood: weighted status distribution
        mood = {
            'ceo':    [('PRESENT', 75), ('REMOTE', 18), ('ABSENT', 3), ('LEAVE', 4)],
            'hr1':    [('PRESENT', 78), ('REMOTE', 15), ('ABSENT', 4), ('LEAVE', 3)],
            'hr2':    [('PRESENT', 70), ('REMOTE', 18), ('ABSENT', 8), ('LEAVE', 4)],
            'hr3':    [('PRESENT', 80), ('REMOTE', 12), ('ABSENT', 5), ('LEAVE', 3)],
            'it1':    [('PRESENT', 60), ('REMOTE', 32), ('ABSENT', 4), ('LEAVE', 4)],
            'it2':    [('PRESENT', 70), ('REMOTE', 22), ('ABSENT', 5), ('LEAVE', 3)],
            'it3':    [('PRESENT', 76), ('REMOTE', 14), ('ABSENT', 7), ('LEAVE', 3)],
            'it4':    [('PRESENT', 55), ('REMOTE', 38), ('ABSENT', 4), ('LEAVE', 3)],
            'sales1': [('PRESENT', 82), ('REMOTE',  8), ('ABSENT', 6), ('LEAVE', 4)],
            'sales2': [('PRESENT', 72), ('REMOTE', 12), ('ABSENT', 10), ('LEAVE', 6)],
            'sales3': [('PRESENT', 78), ('REMOTE', 10), ('ABSENT', 8), ('LEAVE', 4)],
            'sales4': [('PRESENT', 88), ('REMOTE',  4), ('ABSENT', 5), ('LEAVE', 3)],
            'sales5': [('PRESENT', 85), ('REMOTE',  8), ('ABSENT', 4), ('LEAVE', 3)],
            'inv1':   [('PRESENT', 80), ('REMOTE', 10), ('ABSENT', 6), ('LEAVE', 4)],
            'inv2':   [('PRESENT', 76), ('REMOTE',  4), ('ABSENT', 14), ('LEAVE', 6)],
            'inv3':   [('PRESENT', 90), ('REMOTE',  2), ('ABSENT', 5), ('LEAVE', 3)],
        }

        days = list(workdays(date(2026, 1, 5), days_ago(1)))

        bulk = []
        for key, user in users.items():
            weights = mood.get(key, [('PRESENT', 80), ('REMOTE', 10), ('ABSENT', 7), ('LEAVE', 3)])
            statuses, w = zip(*weights)
            # Skip days before the employee's start_date
            start = user.start_date
            for day in days:
                if day < start:
                    continue
                status = rng.choices(statuses, weights=w, k=1)[0]
                bulk.append(Attendance(employee=user, date=day, status=status))
        Attendance.objects.bulk_create(bulk, ignore_conflicts=True)

    # ──────────────────────────────────────────────────────────────
    # Leave Requests
    # ──────────────────────────────────────────────────────────────

    def _leave_requests(self, users, depts):
        hr1 = users['hr1']
        specs = [
            # (emp_key, dept_slug, type, from_d, to_d, status, approved_by)
            ('hr2',    'hr',         'VACATION', date(2026, 1, 20), date(2026, 1, 24), 'APPROVED', hr1),
            ('sales2', 'sales',      'SICK',     date(2026, 2, 3),  date(2026, 2, 5),  'APPROVED', hr1),
            ('it3',    'it',         'VACATION', date(2026, 2, 16), date(2026, 2, 23), 'APPROVED', hr1),
            ('inv2',   'inventory',  'UNPAID',   date(2026, 3, 2),  date(2026, 3, 6),  'REJECTED', hr1),
            ('sales3', 'sales',      'VACATION', date(2026, 3, 23), date(2026, 3, 31), 'APPROVED', hr1),
            ('hr3',    'hr',         'SICK',     date(2026, 4, 8),  date(2026, 4, 10), 'APPROVED', hr1),
            ('it2',    'it',         'VACATION', date(2026, 4, 13), date(2026, 4, 20), 'APPROVED', hr1),
            ('sales1', 'sales',      'VACATION', date(2026, 4, 27), date(2026, 5, 1),  'APPROVED', hr1),
            # Currently on leave (overlaps today 2026-05-19) – feeds CEO HR summary "active on leave"
            ('sales2', 'sales',      'VACATION', date(2026, 5, 18), date(2026, 5, 22), 'APPROVED', hr1),
            ('inv2',   'inventory',  'SICK',     date(2026, 5, 18), date(2026, 5, 20), 'APPROVED', hr1),
            # Pending – needs CEO/HR approval
            ('sales4', 'sales',      'VACATION', date(2026, 5, 25), date(2026, 5, 29), 'PENDING',  None),
            ('hr2',    'hr',         'VACATION', date(2026, 6, 1),  date(2026, 6, 12), 'PENDING',  None),
            ('it1',    'it',         'VACATION', date(2026, 6, 8),  date(2026, 6, 19), 'PENDING',  None),
            # Approved future
            ('sales3', 'sales',      'VACATION', date(2026, 6, 15), date(2026, 6, 26), 'APPROVED', hr1),
            ('inv1',   'inventory',  'VACATION', date(2026, 6, 22), date(2026, 6, 30), 'APPROVED', hr1),
        ]
        for emp_key, dept_slug, ltype, f, t, status, approver in specs:
            LeaveRequest.objects.create(
                employee=users[emp_key], department=depts[dept_slug],
                type=ltype, from_date=f, to_date=t,
                status=status, approved_by=approver,
                reason='Planned leave request',
            )

    # ──────────────────────────────────────────────────────────────
    # Contracts
    # ──────────────────────────────────────────────────────────────

    def _contracts(self, users, depts):
        # (key, dept_slug, type, start, end, salary)
        specs = [
            ('ceo',    None,         'EMPLOYMENT', date(2021, 5, 1),  None,                35000),
            ('hr1',    'hr',         'EMPLOYMENT', date(2024, 5, 19), None,                12000),
            ('hr2',    'hr',         'EMPLOYMENT', date(2025, 4, 14), None,                 8500),
            ('hr3',    'hr',         'EMPLOYMENT', date(2026, 2, 10), None,                 7800),
            ('it1',    'it',         'EMPLOYMENT', date(2023, 12, 1), None,                14000),
            ('it2',    'it',         'EMPLOYMENT', date(2025, 1, 6),  None,                11000),
            ('it3',    'it',         'EMPLOYMENT', date(2025, 11, 4), date(2026, 11, 3),    8000),
            # Contractor with contract ending June 2026 – feeds "expiring soon" workflow
            ('it4',    'it',         'CONTRACTOR', date(2026, 3, 16), date(2026, 6, 30),   10500),
            ('sales1', 'sales',      'EMPLOYMENT', date(2024, 3, 11), None,                10000),
            ('sales2', 'sales',      'EMPLOYMENT', date(2025, 5, 19), None,                 7500),
            ('sales3', 'sales',      'EMPLOYMENT', date(2025, 7, 23), None,                 7500),
            ('sales4', 'sales',      'CONTRACTOR', date(2026, 2, 18), date(2026, 7, 31),    6000),
            ('sales5', 'sales',      'EMPLOYMENT', date(2026, 5, 4),  None,                 7500),
            ('inv1',   'inventory',  'EMPLOYMENT', date(2024, 9, 26), None,                11000),
            ('inv2',   'inventory',  'EMPLOYMENT', date(2025, 11, 20), None,                7000),
            ('inv3',   'inventory',  'EMPLOYMENT', date(2026, 5, 11), None,                 6200),
        ]
        for i, (key, dept_slug, ctype, start, end, salary) in enumerate(specs, start=1):
            Contract.objects.create(
                contract_number=f'CTR-2026-{i:04d}',
                employee=users[key],
                department=depts.get(dept_slug) if dept_slug else None,
                type=ctype, start_date=start, end_date=end,
                salary_ron=Decimal(str(salary)),
            )

    # ──────────────────────────────────────────────────────────────
    # Payroll – Jan, Feb, Mar, Apr (paid) and May 2026 (unpaid)
    # ──────────────────────────────────────────────────────────────

    def _payroll(self, users):
        months = [
            date(2026, 1, 1),
            date(2026, 2, 1),
            date(2026, 3, 1),
            date(2026, 4, 1),
            date(2026, 5, 1),
            date(2026, 6, 1),
        ]
        bulk = []
        for user in users.values():
            gross = float(user.salary_ron)
            net = round(gross * 0.685, 2)  # ~31.5% tax
            for month in months:
                if month < user.start_date.replace(day=1):
                    continue  # not yet employed
                bulk.append(PayrollEntry(
                    employee=user, month=month,
                    gross_salary_ron=Decimal(str(gross)),
                    net_salary_ron=Decimal(str(net)),
                    paid=(month < date(2026, 5, 1)),
                ))
        PayrollEntry.objects.bulk_create(bulk, ignore_conflicts=True)

    # ──────────────────────────────────────────────────────────────
    # Tickets & Comments
    # Created_at is auto_now_add, so we save() the rows then .update()
    # to backdate – this makes the 6-week trend chart show variation.
    # ──────────────────────────────────────────────────────────────

    def _tickets(self, users, depts):
        it_dept = depts['it']
        it1, it2, it3, it4 = users['it1'], users['it2'], users['it3'], users['it4']

        # Older history (Jan–March) – all RESOLVED, fills out the tickets table
        # Format: (title, priority, requested_by_key, assigned_to, created, resolved)
        history = [
            ('Outlook calendar sync failing',       'MEDIUM', 'hr1',    it2, date(2026, 1, 9),  date(2026, 1, 10)),
            ('Slack notifications stopped',         'LOW',    'sales1', it3, date(2026, 1, 14), date(2026, 1, 16)),
            ('Domain controller restart needed',    'URGENT', 'it1',    it2, date(2026, 1, 22), date(2026, 1, 22)),
            ('VPN client install on new laptop',    'LOW',    'sales2', it3, date(2026, 2, 2),  date(2026, 2, 3)),
            ('Power supply replacement – desk 3',   'MEDIUM', 'inv1',   it1, date(2026, 2, 12), date(2026, 2, 15)),
            ('Phishing email reported',             'HIGH',   'hr2',    it1, date(2026, 2, 18), date(2026, 2, 19)),
            ('License renewal – Office 365 batch',  'MEDIUM', 'hr1',    it2, date(2026, 2, 25), date(2026, 2, 27)),
            ('SSL certificate renewal',             'HIGH',   'it1',    it1, date(2026, 3, 4),  date(2026, 3, 5)),
            ('SharePoint quota exceeded',           'MEDIUM', 'sales1', it3, date(2026, 3, 11), date(2026, 3, 13)),
            ('Conference room screen flicker',      'LOW',    'sales3', it3, date(2026, 3, 19), date(2026, 3, 22)),
            ('Database backup script error',        'URGENT', 'it2',    it2, date(2026, 3, 24), date(2026, 3, 24)),
            ('Onboard new sales rep – sales4',      'LOW',    'hr1',    it3, date(2026, 3, 29), date(2026, 4, 1)),
        ]

        # 6-week trend window: Apr 13 → May 24
        # Mix RESOLVED + OPEN/IN_PROGRESS, weighted toward more open closer to today.
        trend = [
            # Week of Apr 13
            ('VPN connection dropping intermittently',  'HIGH',   'sales1', it1, date(2026, 4, 13), date(2026, 4, 14)),
            ('Email client crashing on startup',        'MEDIUM', 'hr1',    it2, date(2026, 4, 14), date(2026, 4, 16)),
            ('Laptop keyboard not responding',          'HIGH',   'sales2', it1, date(2026, 4, 15), date(2026, 4, 16)),
            ('Printer offline – Sales floor',           'MEDIUM', 'sales3', it3, date(2026, 4, 16), date(2026, 4, 17)),
            ('Cannot access shared drive',              'HIGH',   'hr2',    it2, date(2026, 4, 17), date(2026, 4, 18)),

            # Week of Apr 20
            ('New employee laptop setup',               'LOW',    'hr1',    it3, date(2026, 4, 20), date(2026, 4, 21)),
            ('Monitor flickering – Finance desk',       'MEDIUM', 'inv1',   it1, date(2026, 4, 21), date(2026, 4, 22)),
            ('Wi-Fi dead zone in Warehouse',            'URGENT', 'inv2',   it2, date(2026, 4, 22), date(2026, 4, 23)),
            ('Software license expired – Adobe',        'MEDIUM', 'sales1', it1, date(2026, 4, 23), date(2026, 4, 24)),
            ('Backup job failing nightly',              'URGENT', 'it2',    it1, date(2026, 4, 24), date(2026, 4, 24)),
            ('Mouse double-click misbehaving',          'LOW',    'sales2', it3, date(2026, 4, 25), date(2026, 4, 26)),

            # Week of Apr 27
            ('Antivirus false positive blocking app',   'MEDIUM', 'sales4', it3, date(2026, 4, 27), date(2026, 4, 28)),
            ('Remote desktop cert expired',             'HIGH',   'hr1',    it2, date(2026, 4, 28), date(2026, 4, 29)),
            ('Cisco switch port blinking amber',        'HIGH',   'it2',    it1, date(2026, 4, 29), date(2026, 4, 30)),
            ('CRM slow loading > 10 s',                 'HIGH',   'sales2', it1, date(2026, 4, 30), date(2026, 5, 2)),
            ('Zoom audio choppy on meeting room PC',    'MEDIUM', 'sales1', it3, date(2026, 5, 1),  date(2026, 5, 2)),
            ('Onboard new IT contractor – it4',         'LOW',    'hr1',    it3, date(2026, 5, 2),  date(2026, 5, 4)),
            ('GitHub Enterprise login loop',            'HIGH',   'it2',    it1, date(2026, 5, 3),  date(2026, 5, 4)),

            # Week of May 4
            ('Server room temperature alert',           'URGENT', 'it1',    it2, date(2026, 5, 4),  date(2026, 5, 4)),
            ('Two-factor auth not working on mobile',   'HIGH',   'sales3', it1, date(2026, 5, 5),  date(2026, 5, 6)),
            ('CRM filter export broken',                'MEDIUM', 'sales2', it3, date(2026, 5, 6),  date(2026, 5, 8)),
            ('Data export permission denied – BI tool', 'MEDIUM', 'inv1',   it2, date(2026, 5, 7),  date(2026, 5, 8)),
            ('Onboard new warehouse op – inv3',         'LOW',    'hr1',    it3, date(2026, 5, 8),  date(2026, 5, 11)),
            ('Storage low on file-server-02',           'HIGH',   'it2',    it2, date(2026, 5, 9),  date(2026, 5, 10)),

            # Week of May 11
            ('CRM dashboard chart blank',               'MEDIUM', 'sales1', it1, date(2026, 5, 11), date(2026, 5, 12)),
            ('Slow internet on 3rd floor',              'HIGH',   'sales4', it4, date(2026, 5, 12), date(2026, 5, 13)),
            ('USB-C dock not charging laptop',          'MEDIUM', 'it3',    it1, date(2026, 5, 13), date(2026, 5, 14)),
            ('Phishing email reported',                 'HIGH',   'hr2',    it2, date(2026, 5, 14), date(2026, 5, 14)),
            ('Outlook search not indexing',             'LOW',    'hr3',    it3, date(2026, 5, 15), date(2026, 5, 17)),
            ('Network share map missing after reboot',  'MEDIUM', 'sales2', it2, date(2026, 5, 16), date(2026, 5, 18)),
        ]

        # Currently in progress / open – created in last 5 days
        active = [
            # (title, priority, status, requested_by_key, assigned_to_or_None, created_days_ago)
            ('CRM slow loading > 10 s',                 'HIGH',   'IN_PROGRESS', 'sales2', it1, 6),
            ('Server room temperature alert',           'URGENT', 'IN_PROGRESS', 'it1',    it2, 5),
            ('Storage low on file-server-02',           'HIGH',   'IN_PROGRESS', 'it2',    it2, 4),
            ('Remote desktop cert renewal – batch 2',   'HIGH',   'IN_PROGRESS', 'hr1',    it2, 3),
            ('Cisco switch port blinking amber – core', 'HIGH',   'IN_PROGRESS', 'it2',    it1, 3),
            ('Onboarding – account provisioning',       'LOW',    'OPEN',        'hr1',    None, 3),
            ('Zoom audio issue on meeting room PC',     'MEDIUM', 'OPEN',        'sales1', None, 2),
            ('Two-factor auth not working on mobile',   'HIGH',   'OPEN',        'sales3', None, 2),
            ('Data export permission denied – BI tool', 'MEDIUM', 'OPEN',        'inv1',   None, 2),
            ('Keyboard shortcut broken after Win upd.', 'LOW',    'OPEN',        'hr2',    None, 1),
            ('Request new monitor – Sales Team Lead',   'LOW',    'OPEN',        'sales2', None, 1),
            ('Password reset – forgot credentials',     'MEDIUM', 'OPEN',        'inv2',   None, 1),
            ('Slow internet on 3rd floor – again',      'HIGH',   'OPEN',        'sales4', None, 0),
            ('Request VPN access for remote work',      'LOW',    'OPEN',        'hr2',    None, 0),
        ]

        created_tickets = []  # list of (Ticket instance, requested_by_key)

        # Pass 1 — resolved tickets (history + trend)
        for title, priority, req_key, assignee, created, resolved in history + trend:
            t = Ticket(
                title=title,
                description=f'User reported: {title.lower()}. Please investigate and resolve.',
                department=it_dept,
                priority=priority,
                status='RESOLVED',
                requested_by=users[req_key],
                assigned_to=assignee,
                resolved_at=dt(resolved, hour=16),
            )
            t.save()
            Ticket.objects.filter(pk=t.pk).update(created_at=dt(created, hour=9))
            created_tickets.append((t, req_key))

        # Pass 2 — active tickets
        for title, priority, status_, req_key, assignee, days_back in active:
            created = days_ago(days_back)
            t = Ticket(
                title=title,
                description=f'User reported: {title.lower()}. Please investigate and resolve.',
                department=it_dept,
                priority=priority,
                status=status_,
                requested_by=users[req_key],
                assigned_to=assignee,
                resolved_at=None,
            )
            t.save()
            Ticket.objects.filter(pk=t.pk).update(created_at=dt(created, hour=9))
            created_tickets.append((t, req_key))

        # Comments on a handful of tickets – first ticket from each pass + a couple more
        # Index references rely on creation order above.
        ticket_objects = [t for t, _ in created_tickets]
        sales1 = users['sales1']

        comment_specs = [
            # (ticket_obj, author, body, created_date)
            (ticket_objects[12], it1, 'Identified DHCP lease renewal conflict on the office router. Applied fix and reset client lease.', date(2026, 4, 14)),
            (ticket_objects[12], sales1, 'Working great now, thank you!', date(2026, 4, 14)),
            (ticket_objects[19], it2, 'Rerouted cable to access point 3. Signal now covers full warehouse.', date(2026, 4, 23)),
            (ticket_objects[20], it1, 'Cron job had wrong path after OS upgrade. Corrected and tested.', date(2026, 4, 24)),
            (ticket_objects[-9], it2, 'Cooling unit fan replaced. Temperature back to 21°C.', date(2026, 5, 4)),
            (ticket_objects[-11], it1, 'Profiling DB queries — found N+1 in customer list. Optimising.', days_ago(6)),
            (ticket_objects[-7], it2, 'New cert generated and deployed. Awaiting user confirmation.', days_ago(2)),
            (ticket_objects[-3], it1, 'Reproduced — looks like a Windows update regression. Investigating workaround.', days_ago(1)),
        ]
        for ticket, author, body, d in comment_specs:
            tc = TicketComment.objects.create(ticket=ticket, author=author, body=body)
            TicketComment.objects.filter(pk=tc.pk).update(created_at=dt(d, hour=10))

    # ──────────────────────────────────────────────────────────────
    # System Status  (feeds the IT dashboard system-status panel)
    # ──────────────────────────────────────────────────────────────

    def _system_status(self):
        specs = [
            # (name, uptime_pct, status, last_incident_dt or None)
            ('Web Application',  Decimal('99.95'), 'ONLINE',   None),
            ('API Gateway',      Decimal('99.99'), 'ONLINE',   None),
            ('PostgreSQL DB',    Decimal('99.98'), 'ONLINE',   dt(date(2026, 4, 11), hour=2)),
            ('Email Service',    Decimal('98.50'), 'DEGRADED', dt(days_ago(2),       hour=14)),
            ('File Storage',     Decimal('99.90'), 'ONLINE',   None),
            ('VPN Gateway',      Decimal('99.70'), 'ONLINE',   dt(date(2026, 3, 22), hour=9)),
            ('Print Server',     Decimal('87.30'), 'OFFLINE',  dt(days_ago(5),       hour=8)),
            ('CRM Sync Worker',  Decimal('96.20'), 'DEGRADED', dt(days_ago(1),       hour=11)),
            ('Backup Service',   Decimal('99.40'), 'ONLINE',   dt(days_ago(25),      hour=3)),
        ]
        for name, uptime, status, last_incident in specs:
            SystemStatus.objects.create(
                name=name, uptime_pct=uptime, status=status,
                last_incident_date=last_incident,
            )

    # ──────────────────────────────────────────────────────────────
    # Notifications – backdated to recent days
    # ──────────────────────────────────────────────────────────────

    def _notifications(self, users):
        ceo, hr1, it1, sales1, inv1 = (
            users['ceo'], users['hr1'], users['it1'], users['sales1'], users['inv1']
        )
        specs = [
            # (recipient, title, body, link, is_read, days_back)
            (ceo,    'Q1 Revenue Target Achieved',
                     'Sales hit 112% of Q1 target. Great work team!',
                     '', True, 45),
            (ceo,    'April Revenue: +18% vs March',
                     'Strongest month YTD. Sales channel mix shifted toward Direct.',
                     '/sales', True, 18),
            (ceo,    '3 Leave Requests Pending Approval',
                     'HR has flagged 3 leave requests requiring sign-off.',
                     '/reports', False, 1),
            (ceo,    'Contract Expiring: Vlad Dinescu',
                     'Network Engineer contract expires 2026-06-30. Renewal needed.',
                     '/hr', False, 0),
            (hr1,    'New Hire Onboarded — Paul Voicu',
                     'Warehouse operator started on 2026-05-11. Equipment provisioning in progress.',
                     '/hr', True, 8),
            (hr1,    'Payroll for May Pending',
                     'May payroll has not been marked as paid yet.',
                     '/hr/payroll-summary', False, 1),
            (hr1,    'Pending Leave: Bogdan Popa',
                     'Sales rep requested vacation 2026-05-25 → 2026-05-29.',
                     '/hr/leave-requests', False, 0),
            (it1,    'URGENT: Server Temperature Alert',
                     'Server room temperature exceeded threshold. Ticket opened.',
                     '/it/tickets', False, 5),
            (it1,    'Backup Job Fixed',
                     'Nightly backup running successfully again after midnight patch.',
                     '/it', True, 8),
            (it1,    'Print Server Offline',
                     'Print server reported OFFLINE 5 days ago — pending parts.',
                     '/it', False, 5),
            (sales1, 'Large Order Received',
                     'Acme Corp placed an order of 13,600 RON via eMAG.',
                     '/sales/orders', True, 1),
            (sales1, 'Invoice INV-2026-0042 Overdue',
                     'Payment for Rekall Corp invoice is overdue by 5 days.',
                     '/sales/invoices', False, 0),
            (inv1,   'Low Stock Alert — Patch Cable Cat6',
                     'Stock dropped below threshold (4 < 5). Reorder recommended.',
                     '/inventory', False, 2),
            (inv1,   'Out of Stock — Laser Printer A4',
                     'PRT-001 is at 0 units. June delivery scheduled.',
                     '/inventory', False, 1),
        ]
        for recipient, title, body, link, is_read, days_back in specs:
            n = Notification.objects.create(
                recipient=recipient, title=title, body=body,
                link=link, is_read=is_read,
            )
            Notification.objects.filter(pk=n.pk).update(
                created_at=dt(days_ago(days_back), hour=10)
            )

    # ──────────────────────────────────────────────────────────────
    # Workflows + WorkflowLogs (logs are backdated)
    # ──────────────────────────────────────────────────────────────

    def _workflows(self):
        TT = Workflow.TriggerType
        AT = Workflow.ActionType
        defs = [
            (TT.STOCK_BELOW_MINIMUM,      'Low Stock Alert',           {},
             [AT.NOTIFY_MANAGER, AT.EMAIL_CEO], True,  dt(days_ago(2), 9)),
            (TT.NEW_ORDER_RECEIVED,       'New Order Notification',    {},
             [AT.NOTIFY_MANAGER], True,             dt(days_ago(0), 9)),
            (TT.ORDER_EXCEEDS_THRESHOLD,  'High-Value Order Alert',   {'threshold': 10000},
             [AT.EMAIL_CEO, AT.LOG_TO_AUDIT_TRAIL], True, dt(days_ago(1), 14)),
            (TT.NEW_IT_TICKET,            'Ticket SLA Breach Alert',  {},
             [AT.NOTIFY_MANAGER, AT.EMAIL_CEO], True,    dt(days_ago(0), 11)),
            (TT.CONTRACT_EXPIRES,         'Contract Expiry Warning', {'days_ahead': 30},
             [AT.NOTIFY_MANAGER, AT.EMAIL_CEO], True,    dt(days_ago(3), 8)),
            (TT.WEEKLY_AT_TIME,           'Weekly Sales Digest',     {'day_of_week': 'MON', 'hour': 8},
             [AT.GENERATE_REPORT, AT.EMAIL_CEO], True,   dt(days_ago(1), 8)),
        ]
        workflows = []
        for trigger_type, name, config, actions, active, last_triggered in defs:
            wf = Workflow.objects.create(
                name=name, trigger_type=trigger_type,
                trigger_config=config, actions=list(actions),
                is_active=active, last_triggered_at=last_triggered,
            )
            workflows.append(wf)

        # WorkflowLog entries spanning the last few weeks (backdate triggered_at)
        log_specs = [
            (workflows[0], TT.STOCK_BELOW_MINIMUM, [
                {'action': 'NOTIFY_MANAGER', 'status': 'success', 'message': 'Notified 2 inventory managers'},
                {'action': 'EMAIL_CEO',      'status': 'success', 'message': 'CEO email sent (UPS-001 stock low)'},
            ], True, dt(days_ago(2), 9)),
            (workflows[0], TT.STOCK_BELOW_MINIMUM, [
                {'action': 'NOTIFY_MANAGER', 'status': 'success', 'message': 'Notified 2 inventory managers'},
            ], True, dt(days_ago(7), 10)),
            (workflows[1], TT.NEW_ORDER_RECEIVED, [
                {'action': 'NOTIFY_MANAGER', 'status': 'success', 'message': 'Notified 5 sales reps'},
            ], True, dt(days_ago(0), 9)),
            (workflows[1], TT.NEW_ORDER_RECEIVED, [
                {'action': 'NOTIFY_MANAGER', 'status': 'success', 'message': 'Notified 5 sales reps'},
            ], True, dt(days_ago(1), 14)),
            (workflows[2], TT.ORDER_EXCEEDS_THRESHOLD, [
                {'action': 'EMAIL_CEO',          'status': 'success', 'message': 'Acme Corp 13,600 RON order flagged'},
                {'action': 'LOG_TO_AUDIT_TRAIL', 'status': 'success', 'message': 'Audit entry created'},
            ], True, dt(days_ago(1), 14)),
            (workflows[3], TT.NEW_IT_TICKET, [
                {'action': 'NOTIFY_MANAGER', 'status': 'success', 'message': 'Notified IT lead'},
                {'action': 'EMAIL_CEO',      'status': 'success', 'message': 'CEO email sent (URGENT ticket)'},
            ], True, dt(days_ago(0), 11)),
            (workflows[4], TT.CONTRACT_EXPIRES, [
                {'action': 'NOTIFY_MANAGER', 'status': 'success', 'message': 'HR notified — 2 contracts expiring within 30 days'},
                {'action': 'EMAIL_CEO',      'status': 'success', 'message': 'CEO email sent'},
            ], True, dt(days_ago(3), 8)),
            (workflows[5], TT.WEEKLY_AT_TIME, [
                {'action': 'GENERATE_REPORT', 'status': 'success', 'message': 'Weekly sales digest generated'},
                {'action': 'EMAIL_CEO',       'status': 'success', 'message': 'Digest emailed to CEO'},
            ], True, dt(days_ago(1), 8)),
            # One failure for realism
            (workflows[5], TT.WEEKLY_AT_TIME, [
                {'action': 'GENERATE_REPORT', 'status': 'failure', 'message': 'Report generation timed out'},
            ], False, dt(days_ago(8), 8)),
        ]
        for wf, trigger_type, actions_log, success, triggered_at in log_specs:
            log = WorkflowLog.objects.create(
                workflow=wf, trigger_type=trigger_type,
                actions_log=actions_log, success=success,
            )
            WorkflowLog.objects.filter(pk=log.pk).update(triggered_at=triggered_at)

    # ──────────────────────────────────────────────────────────────
    # Reports
    # ──────────────────────────────────────────────────────────────

    def _reports(self):
        specs = [
            ('Annual Tax Summary',        'annual-tax-summary',     'Finance',   'FY25',     1200, date(2026, 1, 12)),
            ('Monthly Revenue Report',    'monthly-revenue-jan',    'Sales',     'Jan 2026',  142, date(2026, 2, 2)),
            ('HR Headcount Summary',      'hr-headcount-jan',       'HR',        'Jan 2026',   78, date(2026, 2, 4)),
            ('Inventory Stock Report',    'inventory-stock-jan',    'Inventory', 'Jan 2026',   95, date(2026, 2, 5)),
            ('IT Ticket SLA Report',      'it-ticket-sla-jan',      'IT',        'Jan 2026',   56, date(2026, 2, 7)),
            ('Monthly Revenue Report',    'monthly-revenue-feb',    'Sales',     'Feb 2026',  155, date(2026, 3, 2)),
            ('HR Headcount Summary',      'hr-headcount-feb',       'HR',        'Feb 2026',   82, date(2026, 3, 4)),
            ('Quarterly Profit & Loss',   'quarterly-pl-q1',        'Finance',   'Q1 FY26',   318, date(2026, 4, 5)),
            ('Sales Channel Analysis',    'sales-channel-q1',       'Sales',     'Q1 FY26',   204, date(2026, 4, 7)),
            ('Top Customers Report',      'top-customers-q1',       'Sales',     'Q1 FY26',    88, date(2026, 4, 8)),
            ('Monthly Revenue Report',    'monthly-revenue-mar',    'Sales',     'Mar 2026',  168, date(2026, 4, 2)),
            ('Inventory Stock Report',    'inventory-stock-mar',    'Inventory', 'Mar 2026',  102, date(2026, 4, 3)),
            ('IT Ticket SLA Report',      'it-ticket-sla-mar',      'IT',        'Mar 2026',   62, date(2026, 4, 6)),
            ('Employee Attendance Report','employee-attendance-mar','HR',        'Mar 2026',  118, date(2026, 4, 4)),
            ('Monthly Revenue Report',    'monthly-revenue-apr',    'Sales',     'Apr 2026',  182, date(2026, 5, 2)),
            ('HR Headcount Summary',      'hr-headcount-apr',       'HR',        'Apr 2026',   85, date(2026, 5, 3)),
            ('IT Ticket SLA Report',      'it-ticket-sla-apr',      'IT',        'Apr 2026',   68, date(2026, 5, 6)),
            ('Inventory Stock Report',    'inventory-stock-apr',    'Inventory', 'Apr 2026',  108, date(2026, 5, 5)),
            ('Top Customers Report',      'top-customers-apr',      'Sales',     'Apr 2026',   92, date(2026, 5, 4)),
            ('Mid-Month Sales Snapshot',  'sales-snapshot-may',     'Sales',     'May 1–15 2026', 64, date(2026, 5, 16)),
        ]
        Report.objects.bulk_create([
            Report(
                name=name, slug=slug, category=cat,
                period=period, file_size_kb=size,
                generated_at=datetime(d.year, d.month, d.day, 9, 0, tzinfo=tz.utc),
            )
            for name, slug, cat, period, size, d in specs
        ])
