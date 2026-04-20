from django.core.management.base import BaseCommand, CommandError

from api.models import Report
from api.report_utils import generate_report_file


class Command(BaseCommand):
    help = 'Generate a mock report file for the given report slug'

    def add_arguments(self, parser):
        parser.add_argument('slug', type=str, help='Slug of the report to generate')

    def handle(self, *args, **options):
        slug = options['slug']
        try:
            report = Report.objects.get(slug=slug)
        except Report.DoesNotExist:
            raise CommandError(f'Report with slug "{slug}" does not exist.')

        generate_report_file(report)
        self.stdout.write(self.style.SUCCESS(
            f'Generated "{report.name}" → {report.file_path} ({report.file_size_kb} KB)'
        ))
