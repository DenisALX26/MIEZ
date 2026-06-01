from rest_framework import status
from rest_framework.test import APITestCase
from model_bakery import baker
from django.urls import reverse

from api.models import Asset, User


class AssetApiTests(APITestCase):
    def setUp(self):
        self.ceo = baker.make(User, role=User.Role.CEO, username='asset_ceo', email='asset_ceo@example.com')
        self.it_user = baker.make(User, role=User.Role.IT, username='asset_it', email='asset_it@example.com')
        self.hr_user = baker.make(User, role=User.Role.HR, username='asset_hr', email='asset_hr@example.com')
        self.inventory_user = baker.make(
            User,
            role=User.Role.INVENTORY,
            username='asset_inventory',
            email='asset_inventory@example.com',
        )

        self.assets_url = reverse('asset_list_create')

    def test_list_returns_assets_for_ceo_and_it_only(self):
        baker.make(
            Asset,
            _quantity=2,
            assigned_to=self.it_user,
            status=Asset.Status.ASSIGNED,
        )

        self.client.force_authenticate(user=self.hr_user)
        response = self.client.get(self.assets_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.it_user)
        response = self.client.get(self.assets_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertTrue({
            'id',
            'name',
            'serial_number',
            'category',
            'assigned_to',
            'assigned_to_username',
            'assigned_to_name',
            'status',
            'notes',
            'created_at',
        }.issubset(response.data[0].keys()))

    def test_create_asset_returns_serialized_asset(self):
        payload = {
            'name': 'CEO Laptop',
            'serial_number': 'ASSET-TEST-001',
            'category': Asset.Category.LAPTOP,
            'assigned_to': self.ceo.id,
            'status': Asset.Status.ASSIGNED,
            'notes': 'Executive device',
        }

        self.client.force_authenticate(user=self.ceo)
        response = self.client.post(self.assets_url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], payload['name'])
        self.assertEqual(response.data['serial_number'], payload['serial_number'])
        self.assertEqual(response.data['assigned_to'], self.ceo.id)
        self.assertEqual(response.data['assigned_to_username'], self.ceo.username)
        self.assertEqual(response.data['assigned_to_name'], self.ceo.get_full_name() or self.ceo.username)

    def test_create_asset_rejects_duplicate_serial_number(self):
        baker.make(Asset, serial_number='ASSET-TEST-002')

        self.client.force_authenticate(user=self.it_user)
        response = self.client.post(
            self.assets_url,
            {
                'name': 'Duplicate Asset',
                'serial_number': 'ASSET-TEST-002',
                'category': Asset.Category.MONITOR,
                'status': Asset.Status.AVAILABLE,
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('serial_number', response.data['field_errors'])

    def test_detail_update_and_delete_work_for_it_and_ceo(self):
        asset = baker.make(
            Asset,
            name='Old Laptop',
            serial_number='ASSET-TEST-003',
            category=Asset.Category.LAPTOP,
            assigned_to=self.it_user,
            status=Asset.Status.ASSIGNED,
        )
        detail_url = reverse('asset_detail', kwargs={'id': asset.id})

        self.client.force_authenticate(user=self.inventory_user)
        response = self.client.patch(detail_url, {'name': 'Blocked Update'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.it_user)
        response = self.client.patch(
            detail_url,
            {
                'name': 'Updated Laptop',
                'status': Asset.Status.MAINTENANCE,
                'notes': 'Needs screen replacement',
                'assigned_to': self.ceo.id,
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Updated Laptop')
        self.assertEqual(response.data['status'], Asset.Status.MAINTENANCE)
        self.assertEqual(response.data['assigned_to'], self.ceo.id)
        self.assertEqual(response.data['assigned_to_username'], self.ceo.username)

        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Asset.objects.filter(id=asset.id).exists())

    def test_detail_returns_404_for_missing_asset(self):
        self.client.force_authenticate(user=self.ceo)
        response = self.client.get(reverse('asset_detail', kwargs={'id': 999999}))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)