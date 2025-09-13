from rest_framework import permissions


class IsAdminUser(permissions.BasePermission):
    """Permission class that only allows admin users"""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_admin()


class IsOwnerOrAdmin(permissions.BasePermission):
    """Permission class that allows owners or admin users"""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Admin users can access any object
        if request.user.is_admin():
            return True
        
        # For Report objects, check if user is the reporter
        if hasattr(obj, 'reported_by'):
            return obj.reported_by == request.user
        
        # For other objects, only admin access
        return False


class IsCitizenOrAdmin(permissions.BasePermission):
    """Permission class that allows citizens and admin users"""
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            (request.user.is_citizen() or request.user.is_admin())
        )


class IsAdminOrReadOnly(permissions.BasePermission):
    """Permission class that allows read access to all authenticated users, 
    but write access only to admin users"""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Read permissions for authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions only for admin users
        return request.user.is_admin()