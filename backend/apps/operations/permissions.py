from rest_framework.permissions import BasePermission


class StaffOperationPermission(BasePermission):
    required_permission = "operations.view_driver"

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated or not user.is_staff:
            return False
        if user.is_superuser:
            return True
        required = getattr(view, "required_permission", self.required_permission)
        if isinstance(required, (tuple, list)):
            return any(user.has_perm(permission) for permission in required)
        return user.has_perm(required)

