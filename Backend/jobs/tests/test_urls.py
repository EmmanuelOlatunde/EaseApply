from django.urls import reverse, resolve
from django.test import TestCase
from users.views import (
    RegisterView,
    LoginView,
    LogoutView,
    ProfileView,
    ChangePasswordView
)
from rest_framework.test import APIClient
from rest_framework import status
from users.models import User
from rest_framework.authtoken.models import Token


class TestUserURLs(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='Testpass123!'
        )
        self.token = Token.objects.create(user=self.user)

    def test_register_url_resolution(self):
        url = reverse('users:register')
        resolver = resolve(url)
        assert resolver.func.view_class == RegisterView
        assert resolver.namespace == 'users'
        assert resolver.url_name == 'register'
        assert url == '/register/'

    def test_login_url_resolution(self):
        url = reverse('users:login')
        resolver = resolve(url)
        assert resolver.func.view_class == LoginView
        assert resolver.namespace == 'users'
        assert resolver.url_name == 'login'
        assert url == '/login/'

    def test_logout_url_resolution(self):
        url = reverse('users:logout')
        resolver = resolve(url)
        assert resolver.func.view_class == LogoutView
        assert resolver.namespace == 'users'
        assert resolver.url_name == 'logout'
        assert url == '/logout/'

    def test_profile_url_resolution(self):
        url = reverse('users:profile')
        resolver = resolve(url)
        assert resolver.func.view_class == ProfileView
        assert resolver.namespace == 'users'
        assert resolver.url_name == 'profile'
        assert url == '/profile/'

    def test_change_password_url_resolution(self):
        url = reverse('users:change-password')
        resolver = resolve(url)
        assert resolver.func.view_class == ChangePasswordView
        assert resolver.namespace == 'users'
        assert resolver.url_name == 'change-password'
        assert url == '/change-password/'

    def test_register_url_access_unauthenticated(self):
        response = self.client.post(reverse('users:register'), {
            'email': 'newuser@example.com',
            'username': 'newuser',
            'password': 'Testpass123!',
            'password_confirm': 'Testpass123!'
        })
        assert response.status_code == status.HTTP_201_CREATED

    def test_login_url_access_unauthenticated(self):
        response = self.client.post(reverse('users:login'), {
            'email': 'test@example.com',
            'password': 'Testpass123!'
        })
        assert response.status_code == status.HTTP_200_OK

    def test_logout_url_access_authenticated(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.post(reverse('users:logout'))
        assert response.status_code == status.HTTP_200_OK

    def test_logout_url_access_unauthenticated(self):
        response = self.client.post(reverse('users:logout'))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_profile_url_access_authenticated(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.get(reverse('users:profile'))
        assert response.status_code == status.HTTP_200_OK

    def test_profile_url_access_unauthenticated(self):
        response = self.client.get(reverse('users:profile'))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_change_password_url_access_authenticated(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.put(reverse('users:change-password'), {
            'old_password': 'Testpass123!',
            'new_password': 'Newpass456!'
        })
        assert response.status_code == status.HTTP_200_OK

    def test_change_password_url_access_unauthenticated(self):
        response = self.client.put(reverse('users:change-password'), {
            'old_password': 'Testpass123!',
            'new_password': 'Newpass456!'
        })
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_invalid_url(self):
        response = self.client.get('/invalid-url/')
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_url_namespace(self):
        urls = [
            'users:register',
            'users:login',
            'users:logout',
            'users:profile',
            'users:change-password'
        ]
        for url_name in urls:
            url = reverse(url_name)
            assert url.startswith('/')
            assert resolve(url).namespace == 'users'

    def test_url_methods(self):
        # Test allowed HTTP methods for each endpoint
        url_methods = {
            'users:register': ['POST'],
            'users:login': ['POST'],
            'users:logout': ['POST'],
            'users:profile': ['GET', 'PUT'],
            'users:change-password': ['PUT']
        }
        
        for url_name, allowed_methods in url_methods.items():
            url = reverse(url_name)
            self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
            
            # Test allowed methods
            for method in allowed_methods:
                if method == 'GET':
                    response = self.client.get(url)
                elif method == 'POST':
                    response = self.client.post(url, {})
                elif method == 'PUT':
                    response = self.client.put(url, {})
                # Skip authentication checks for register and login
                if url_name in ['users:register', 'users:login']:
                    assert response.status_code in [status.HTTP_200_OK, status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST]
                else:
                    assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]

            # Test disallowed methods
            all_methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']
            disallowed_methods = [m for m in all_methods if m not in allowed_methods]
            for method in disallowed_methods:
                if method == 'GET':
                    response = self.client.get(url)
                elif method == 'POST':
                    response = self.client.post(url, {})
                elif method == 'PUT':
                    response = self.client.put(url, {})
                elif method == 'DELETE':
                    response = self.client.delete(url)
                elif method == 'PATCH':
                    response = self.client.patch(url, {})
                assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_url_trailing_slash(self):
        urls = [
            ('users:register', '/register/'),
            ('users:login', '/login/'),
            ('users:logout', '/logout/'),
            ('users:profile', '/profile/'),
            ('users:change-password', '/change-password/')
        ]
        for url_name, expected_path in urls:
            url = reverse(url_name)
            assert url == expected_path
            # Test without trailing slash
            no_slash_url = url.rstrip('/')
            response = self.client.get(no_slash_url)
            assert response.status_code in [status.HTTP_200_OK, status.HTTP_301_MOVED_PERMANENTLY, status.HTTP_401_UNAUTHORIZED, status.HTTP_405_METHOD_NOT_ALLOWED]