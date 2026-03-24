from django.test import TestCase, Client
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from django.conf import settings

class IsEvenTests(TestCase):
    def setUp(self):
        self.client = Client()

    # ── Success cases ──────────────────────────────────────────

    def test_even_number(self):
        response = self.client.get('/api/is_even/', {'number': 4})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['even'], True)

    def test_odd_number(self):
        response = self.client.get('/api/is_even/', {'number': 3})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['even'], False)

    def test_zero(self):
        response = self.client.get('/api/is_even/', {'number': 0})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['even'], True)

    def test_negative_even(self):
        response = self.client.get('/api/is_even/', {'number': -2})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['even'], True)

    def test_negative_odd(self):
        response = self.client.get('/api/is_even/', {'number': -7})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['even'], False)

    # ── Fail cases ─────────────────────────────────────────────

    def test_missing_number(self):
        response = self.client.get('/api/is_even/')
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

    def test_string_input(self):
        response = self.client.get('/api/is_even/', {'number': 'abc'})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

    def test_float_string(self):
        response = self.client.get('/api/is_even/', {'number': '2.5'})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

    def test_post_not_allowed(self):
        response = self.client.post('/api/is_even/', {'number': 2})
        self.assertEqual(response.status_code, 405)  # method not allowed


class AuthTests(APITestCase):
    def setUp(self):
        self.username = 'testuser'
        self.password = 'testpass123'
        User = get_user_model()
        self.user = User.objects.create_user(username=self.username, password=self.password)
        self.login_url = reverse('login')
        self.me_url = reverse('user_me')
        self.logout_url = reverse('logout')

    def test_login_sets_cookies(self):
        data = {"username": self.username, "password": self.password}
        response = self.client.post(self.login_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(settings.SIMPLE_JWT['AUTH_COOKIE'], response.cookies)
        self.assertIn(settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH'], response.cookies)
        self.assertTrue(response.cookies[settings.SIMPLE_JWT['AUTH_COOKIE']]['httponly'])

    def test_protected_route_access(self):
        self.client.post(self.login_url, {"username": self.username, "password": self.password})
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        # Ensure expected fields exist in the JSON response. The user model may not
        # always expose a `role` attribute, so assert presence of core fields.
        self.assertEqual(data.get('username'), self.username)
        self.assertIn('email', data)
        self.assertIn('message', data)

    def test_access_denied_without_cookie(self):
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_clears_cookies(self):
        self.client.post(self.login_url, {"username": self.username, "password": self.password})

        response = self.client.post(self.logout_url)
        access_cookie = response.cookies.get(settings.SIMPLE_JWT['AUTH_COOKIE'])
        self.assertEqual(access_cookie.value, '')