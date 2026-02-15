# dashboard_access/permissions.py
from rest_framework.permissions import BasePermission

from dashboard_accessapp.enums import PermissionLevel
from dashboard_accessapp.services.permissions import has_admin_perm


class DashboardPermission(BasePermission):
    """
    Attach required_permission_code + required_level on the view.

    Example:
        required_permission_code = "content.course"
        required_level = PermissionLevel.WRITE
    """

    message = "You do not have permission to perform this action."

    def has_permission(self, request, view):
        code = getattr(view, "required_permission_code", None)
        level = getattr(view, "required_level", PermissionLevel.READ)

        if not code:
            # If a view forgot to declare permissions, deny by default for safety.
            return False

        return has_admin_perm(request.user, code, level)