from rest_framework import permissions


class IsAuthenticatedAndActive(permissions.BasePermission):
    """Permission for authenticated and active users"""
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_active
        )


class IsOwnerOrStaffReadOnly(permissions.BasePermission):
    """Permission for owners to edit, staff to read, others denied"""
    
    def has_object_permission(self, request, view, obj):
        # Staff can read
        if request.user.is_staff and request.method in permissions.SAFE_METHODS:
            return True
        # Owner can do anything
        return hasattr(obj, 'user') and obj.user == request.user


class IsCreatorOrReadOnly(permissions.BasePermission):
    """Permission for creators to edit their content"""
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return hasattr(obj, 'created_by') and obj.created_by == request.user


class IsSuperUserOrReadOnly(permissions.BasePermission):
    """Permission for superusers to edit, others to read only"""
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_superuser
    

class IsOwnerOrReadOnly(permissions.BasePermission):
    """Allow owners to edit, others read-only"""
    
    def has_object_permission(self, request, view, obj):
        # Read-only permissions are allowed for safe methods (GET, HEAD, OPTIONS)
        if request.method in permissions.SAFE_METHODS:
            return True

        # Only allow edit if the requesting user is the owner
        return hasattr(obj, 'owner') and obj.owner == request.user

class IsOwner(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to access it.
    """
    
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user