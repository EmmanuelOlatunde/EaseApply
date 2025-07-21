from django.test import TestCase
from django.contrib.auth import get_user_model
from users.models import UserProfile

User = get_user_model()


class UserModelTests(TestCase):
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
    
    def test_user_creation(self):
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertEqual(self.user.username, 'testuser')
        self.assertTrue(self.user.check_password('testpass123'))
    
    def test_user_str_method(self):
        self.assertEqual(str(self.user), 'test@example.com')
    
    def test_profile_creation(self):
        profile = UserProfile.objects.create(user=self.user)
        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.timezone, 'UTC')