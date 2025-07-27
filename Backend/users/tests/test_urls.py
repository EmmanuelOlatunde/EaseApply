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
from rest_framework_simplejwt.tokens import AccessToken


class TestUserURLs(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='Testpass123!'
        )
        
        self.jwt_token = AccessToken.for_user(self.user)

    def test_register_url_resolution(self):
        url = reverse('users:register')
        resolver = resolve(url)
        assert resolver.func.view_class == RegisterView
        assert resolver.namespace == 'users'
        assert resolver.url_name == 'register'
        assert url == '/users/register/'

    def test_login_url_resolution(self):
        url = reverse('users:login')
        resolver = resolve(url)
        assert resolver.func.view_class == LoginView
        assert resolver.namespace == 'users'
        assert resolver.url_name == 'login'
        assert url == '/users/login/'

    def test_logout_url_resolution(self):
        url = reverse('users:logout')
        resolver = resolve(url)
        assert resolver.func.view_class == LogoutView
        assert resolver.namespace == 'users'
        assert resolver.url_name == 'logout'
        assert url == '/users/logout/'

    def test_profile_url_resolution(self):
        url = reverse('users:profile')
        resolver = resolve(url)
        assert resolver.func.view_class == ProfileView
        assert resolver.namespace == 'users'
        assert resolver.url_name == 'profile'
        assert url == '/users/profile/'

    def test_change_password_url_resolution(self):
        url = reverse('users:change-password')
        resolver = resolve(url)
        assert resolver.func.view_class == ChangePasswordView
        assert resolver.namespace == 'users'
        assert resolver.url_name == 'change-password'
        assert url == '/users/change-password/'

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
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(self.jwt_token)}')
        response = self.client.post(reverse('users:logout'))
        assert response.status_code == status.HTTP_200_OK

    def test_logout_url_access_unauthenticated(self):
        response = self.client.post(reverse('users:logout'))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_profile_url_access_authenticated(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(self.jwt_token)}')
        response = self.client.get(reverse('users:profile'))
        assert response.status_code == status.HTTP_200_OK

    def test_profile_url_access_unauthenticated(self):
        response = self.client.get(reverse('users:profile'))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_change_password_url_access_authenticated(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(self.jwt_token)}')
        response = self.client.put(reverse('users:change-password'), {
            'old_password': 'Testpass123!',
            'new_password': 'Newpass456!',
            'new_password_confirm': 'Newpass456!'
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
            'users:profile': ['GET', 'PUT', 'PATCH'],  # Add PATCH to allowed methods
            'users:change-password': ['PUT']
        }
        
        for url_name, allowed_methods in url_methods.items():
            url = reverse(url_name)
            
            # Only set token for authenticated endpoints
            if url_name not in ['users:register', 'users:login']:
                self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(self.jwt_token)}')
            else:
                self.client.credentials()  # Clear token for register/login
            
            # First test disallowed methods to avoid state changes
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
                    
                # For unauthenticated endpoints, disallowed methods should return 405
                # For authenticated endpoints, disallowed methods with valid token should return 405
                assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED, \
                    f"Expected 405 for {method} {url_name}, got {response.status_code}"
            
            # Then test allowed methods
            for method in allowed_methods:
                if method == 'GET':
                    response = self.client.get(url)
                elif method == 'POST':
                    # Provide minimal valid data for POST requests
                    data = {}
                    if url_name == 'users:register':
                        data = {
                            'email': 'test2@example.com',
                            'username': 'testuser2',
                            'password': 'Testpass123!',
                            'password_confirm': 'Testpass123!'
                        }
                    elif url_name == 'users:login':
                        data = {
                            'email': 'test@example.com',
                            'password': 'Testpass123!'
                        }
                    response = self.client.post(url, data)
                elif method == 'PUT':
                    # Provide valid data for PUT requests
                    data = {}
                    if url_name == 'users:profile':
                        data = {'username': 'newusername'}
                    elif url_name == 'users:change-password':
                        data = {
                            'old_password': 'Testpass123!',
                            'new_password': 'Newpass456!',
                            'new_password_confirm': 'Newpass456!'
                        }
                    response = self.client.put(url, data)
                elif method == 'PATCH':  # Add PATCH handling
                    data = {}
                    if url_name == 'users:profile':
                        data = {'username': 'newusername'}
                    response = self.client.patch(url, data)
                
                # Check expected status codes
                if url_name in ['users:register', 'users:login']:
                    assert response.status_code in [
                        status.HTTP_200_OK, 
                        status.HTTP_201_CREATED, 
                        status.HTTP_400_BAD_REQUEST
                    ], f"Unexpected status for {method} {url_name}: {response.status_code}"
                else:
                    assert response.status_code in [
                        status.HTTP_200_OK, 
                        status.HTTP_400_BAD_REQUEST
                    ], f"Unexpected status for {method} {url_name}: {response.status_code}"



    def test_url_trailing_slash(self):
        urls = [
            ('users:register', '/users/register/'),
            ('users:login', '/users/login/'),
            ('users:logout', '/users/logout/'),
            ('users:profile', '/users/profile/'),
            ('users:change-password', '/users/change-password/')
        ]
        for url_name, expected_path in urls:
            url = reverse(url_name)
            assert url == expected_path
            # Test without trailing slash
            no_slash_url = url.rstrip('/')
            response = self.client.get(no_slash_url)
            assert response.status_code in [status.HTTP_200_OK, status.HTTP_301_MOVED_PERMANENTLY, status.HTTP_401_UNAUTHORIZED, status.HTTP_405_METHOD_NOT_ALLOWED]