from django.test import TestCase
from users.serializers import UserRegistrationSerializer


class UserSerializerTests(TestCase):
    
    def test_registration_serializer_valid_data(self):
        data = {
            'email': 'test@example.com',
            'username': 'testuser',
            'password': 'strongpass123',
            'password_confirm': 'strongpass123',
            'first_name': 'Test',
            'last_name': 'User'
        }
        serializer = UserRegistrationSerializer(data=data)
        self.assertTrue(serializer.is_valid())
    
    def test_registration_serializer_password_mismatch(self):
        data = {
            'email': 'test@example.com',
            'username': 'testuser', 
            'password': 'strongpass123',
            'password_confirm': 'differentpass',
        }
        serializer = UserRegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)

