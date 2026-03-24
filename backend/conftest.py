import pytest
from rest_framework.test import APIClient
from django.contrib.auth.models import User

@pytest.fixture
def api_client():
    """Fixture pentru a simula un browser/client de API"""
    return APIClient()

@pytest.fixture
def test_user(db):
    """Fixture care creează un utilizator de test în baza de date"""
    return User.objects.create_user(
        username='testuser', 
        password='password123', 
        email='test@example.com'
    )

@pytest.fixture
def authenticated_client(api_client, test_user):
    """Fixture care îți dă un client deja logat (folosește cele două de mai sus)"""
    api_client.force_authenticate(user=test_user)
    return api_client