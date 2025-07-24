from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserProfile


class UserProfileInline(admin.StackedInline):
    """Inline profile editing in User admin"""
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom User admin"""
    # Show these fields in the admin list view
    list_display = (
        'email',
        'username',
        'full_name',
        'is_active',
        'is_verified',
        'is_staff',
        'last_login',
        'created_at'
    )
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'is_verified', 'created_at')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('-created_at',)

    # Make these fields read-only in admin
    readonly_fields = ('last_login', 'created_at', 'updated_at')

    # Add profile inline
    inlines = [UserProfileInline]

    # Customize field layout in admin form
    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        ('Personal Info', {
            'fields': ('first_name', 'last_name', 'phone', 'profile_picture', 'bio', 'date_of_birth')
        }),
        ('Verification', {'fields': ('is_verified',)}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Important Dates', {'fields': ('last_login', 'created_at', 'updated_at')}),
    )

    # Fields shown when creating a new user
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2', 'is_active', 'is_staff')
        }),
    )

    def get_inline_instances(self, request, obj=None):
        """Ensure inline appears only if user exists"""
        if not obj:
            return []
        return super().get_inline_instances(request, obj)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Optional standalone profile admin"""
    list_display = ('user', 'timezone', 'language')
    search_fields = ('user__email', 'user__username')
