import tempfile
from pathlib import Path

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from ..models import Report, User


def _make_user(username, role=User.Role.HR, **kwargs):
    return User.objects.create_user(username=username, password='testpass', role=role, **kwargs)


def _make_report(**kwargs):
    defaults = {
        'name': 'Test Report',
        'slug': 'test-report',
        'category': 'HR',
        'period': 'Feb 2026',
        'file_size_kb': 78,
        'generated_at': timezone.now(),
    }
    defaults.update(kwargs)
    return Report.objects.create(**defaults)


class ReportListTests(APITestCase):
    def setUp(self):
        self.user = _make_user('hruser')
        self.client.force_authenticate(user=self.user)
        self.url = reverse('report_list')

    def test_returns_all_reports(self):
        _make_report(slug='rep-1', name='Report 1', category='HR')
        _make_report(slug='rep-2', name='Report 2', category='Sales')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_returns_correct_metadata_fields(self):
        _make_report()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        report = response.data[0]
        for field in ('id', 'name', 'slug', 'category', 'period', 'file_size_kb', 'generated_at', 'file_available'):
            self.assertIn(field, report)

    def test_filter_by_category(self):
        _make_report(slug='hr-rep', name='HR Report', category='HR')
        _make_report(slug='sales-rep', name='Sales Report', category='Sales')
        response = self.client.get(self.url, {'category': 'HR'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['category'], 'HR')

    def test_unauthenticated_returns_401(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ReportDownloadTests(APITestCase):
    def setUp(self):
        self.user = _make_user('hruser2')
        self.client.force_authenticate(user=self.user)

    def _url(self, report_id):
        return reverse('report_download', kwargs={'id': report_id})

    def test_download_returns_file_response(self):
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False, mode='w') as f:
            f.write('Name,Value\nAlice,100\n')
            tmp_path = f.name

        report = _make_report(slug='dl-report', file_path=tmp_path)
        response = self.client.get(self._url(report.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('text/csv', response.get('Content-Type', ''))

    def test_download_returns_404_when_file_path_missing(self):
        report = _make_report(slug='no-file-report', file_path='')
        response = self.client.get(self._url(report.id))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_download_returns_404_when_file_does_not_exist_on_disk(self):
        report = _make_report(slug='ghost-report', file_path='/tmp/nonexistent_miez_report.csv')
        response = self.client.get(self._url(report.id))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_download_returns_404_for_unknown_report(self):
        response = self.client.get(self._url(99999))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class ReportGenerateTests(APITestCase):
    def setUp(self):
        self.ceo = _make_user('ceo_user', role=User.Role.CEO)
        self.hr_user = _make_user('hr_user2', role=User.Role.HR)
        self.report = _make_report(slug='gen-report')

    def _url(self, slug):
        return reverse('report_generate', kwargs={'slug': slug})

    def test_non_ceo_gets_403(self):
        self.client.force_authenticate(user=self.hr_user)
        response = self.client.post(self._url(self.report.slug))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_gets_401(self):
        response = self.client.post(self._url(self.report.slug))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invalid_slug_returns_404(self):
        self.client.force_authenticate(user=self.ceo)
        response = self.client.post(self._url('does-not-exist'))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_valid_slug_triggers_generation_and_updates_generated_at(self):
        self.client.force_authenticate(user=self.ceo)
        before = timezone.now()
        response = self.client.post(self._url(self.report.slug))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.report.refresh_from_db()
        self.assertIsNotNone(self.report.generated_at)
        self.assertGreaterEqual(self.report.generated_at, before)

    def test_valid_slug_returns_report_data(self):
        self.client.force_authenticate(user=self.ceo)
        response = self.client.post(self._url(self.report.slug))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['slug'], self.report.slug)
        self.assertIn('generated_at', response.data)

    def test_admin_user_can_generate(self):
        admin = _make_user('admin_user', role=User.Role.HR, is_staff=True)
        self.client.force_authenticate(user=admin)
        response = self.client.post(self._url(self.report.slug))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
