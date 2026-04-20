from pathlib import Path

from django.conf import settings
from django.utils import timezone

_MOCK_HEADERS = {
    'Sales': 'Date,Product,Channel,Revenue,Units',
    'Finance': 'Period,Revenue,Costs,Gross_Profit,Net_Profit,Margin_pct',
    'Inventory': 'SKU,Product,Opening_Stock,Inbound,Outbound,Closing_Stock,Value',
    'HR': 'Employee_ID,Name,Department,Status,Days_Present,Days_Absent',
    'IT': 'Ticket_ID,Priority,Category,Opened,Resolved,SLA_Met',
}

_MOCK_ROWS = {
    'monthly-revenue': [
        '2026-02-01,Product A,Online,12400,87',
        '2026-02-08,Product B,Retail,9800,54',
        '2026-02-15,Product C,Online,11200,62',
        '2026-02-22,Product D,Partner,11800,71',
    ],
    'quarterly-pl': [
        'Q1 FY26,310000,198000,112000,89000,28.7',
        'Q2 FY26,340000,212000,128000,101000,29.7',
        'Q3 FY26,380000,235000,145000,116000,30.5',
    ],
    'inventory-stock': [
        'SKU-001,Widget A,200,150,180,170,8500',
        'SKU-002,Widget B,80,60,70,70,3500',
        'SKU-003,Gadget X,45,30,40,35,5250',
    ],
    'hr-headcount': [
        'EMP-001,Alice Smith,Engineering,Active,20,0',
        'EMP-002,Bob Jones,Sales,Active,19,1',
        'EMP-003,Carol White,HR,Active,20,0',
    ],
    'it-ticket-sla': [
        'TKT-001,High,Network,2026-02-03,2026-02-03,Yes',
        'TKT-002,Medium,Software,2026-02-05,2026-02-07,Yes',
        'TKT-003,Low,Hardware,2026-02-10,2026-02-15,No',
    ],
    'sales-channel-analysis': [
        '2026-01-01,Product A,Online,41200,298',
        '2026-01-01,Product B,Retail,38900,241',
        '2026-01-01,Product C,Partner,55500,187',
    ],
    'employee-attendance': [
        'EMP-001,Alice Smith,Engineering,Active,20,0',
        'EMP-004,Dave Brown,Marketing,Active,18,2',
        'EMP-005,Eve Davis,Finance,Active,19,1',
    ],
    'top-customers': [
        '2026-01-01,Acme Corp,Online,28400,14',
        '2026-01-01,Globex Ltd,Retail,19800,8',
        '2026-01-01,Initech,Partner,15600,6',
    ],
    'annual-tax-summary': [
        'FY25,1240000,820000,420000,336000,27.1',
    ],
}


def generate_report_file(report, user=None):
    reports_dir = Path(settings.BASE_DIR) / 'reports'
    reports_dir.mkdir(exist_ok=True)

    header = _MOCK_HEADERS.get(report.category, 'Field1,Field2,Field3')
    rows = _MOCK_ROWS.get(report.slug, ['mock,data,row'])
    content = '\n'.join([header] + rows) + '\n'

    file_path = reports_dir / f'{report.slug}.csv'
    file_path.write_text(content, encoding='utf-8')

    size_kb = max(1, file_path.stat().st_size // 1024) if file_path.stat().st_size >= 1024 else 1
    report.file_path = str(file_path)
    report.file_size_kb = size_kb
    report.generated_at = timezone.now()
    if user is not None:
        report.generated_by = user
    report.save(update_fields=['file_path', 'file_size_kb', 'generated_at', 'generated_by'])
