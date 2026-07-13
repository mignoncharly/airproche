from rest_framework.permissions import BasePermission


class CommunicationPermission(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated or not user.is_staff:
            return False
        if user.is_superuser:
            return True
        action = getattr(view, "action", "")
        permission = (
            "notifications.change_emailnotification"
            if action == "retry"
            else "notifications.view_emailnotification"
        )
        return user.has_perm(permission)
