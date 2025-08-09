from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import User, UserProfile


class UserSerializer(serializers.ModelSerializer):
    """Basic user serializer used by Djoser for `user` and `current_user` endpoints"""
    class Meta:
        model = User
        fields = (
            "id", "email", "username", "first_name", "last_name",
            "phone", "is_active", "is_verified", "created_at"
        )
        read_only_fields = ("id", "is_active", "is_verified", "created_at")


class UserRegistrationSerializer(serializers.ModelSerializer):
    """User registration serializer"""
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = (
            'email', 'username', 'password', 'password_confirm',
            'first_name', 'last_name', 'phone'
        )
        extra_kwargs = {
            'email': {'required': True},
            'username': {'required': True}
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        UserProfile.objects.get_or_create(user=user)  # Avoids duplicate profile creation
        return user


class UserLoginSerializer(serializers.Serializer):
    """User login serializer"""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(
            username=attrs.get('email'),
            password=attrs.get('password')
        )
        if not user or not user.is_active:
            raise serializers.ValidationError('Invalid email or password, or account disabled')
        attrs['user'] = user
        return attrs


class UserProfileSerializer(serializers.ModelSerializer):
    """User profile serializer"""
    profile = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name', 'phone',
            'profile_picture', 'is_verified', 'date_of_birth', 'bio',
            'profile', 'created_at'
        )
        read_only_fields = ('id', 'email', 'is_verified', 'created_at')

    def get_profile(self, obj):
        # Use select_related in the view to avoid extra queries
        profile = getattr(obj, 'profile', None)
        if not profile:
            return {}
        return {
            'timezone': profile.timezone,
            'language': profile.language,
            'notification_preferences': profile.notification_preferences,
            'privacy_settings': profile.privacy_settings,
            'social_links': profile.social_links
        }


class ChangePasswordSerializer(serializers.Serializer):
    """Change password serializer"""
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(required=True)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Invalid old password')
        return value

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({"new_password_confirm": "Passwords do not match"})
        return attrs


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ResetPasswordConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(validators=[validate_password])
    new_password_confirm = serializers.CharField()

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({"new_password_confirm": "Passwords do not match"})
        return attrs
