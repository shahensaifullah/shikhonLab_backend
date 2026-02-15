# dashboard_access/services/permissions.py
from django.db.models import Max

from dashboard_accessapp.enums import PermissionLevel
from dashboard_accessapp.models import AdminPermission, RolePermission

def resolve_admin_level(user, permission_code: str) -> int:
    """
    Returns the highest PermissionLevel the user has for a permission_code.

    If no permission is assigned, returns PermissionLevel.NONE.
    """
    if not user or not user.is_authenticated:
        return PermissionLevel.NONE

    # Superuser is always ADMIN
    if getattr(user, "is_superuser", False) is True:
        return PermissionLevel.ADMIN

    # Find the permission row (optional guard: if permission code doesn't exist)
    perm = AdminPermission.objects.filter(code=permission_code, is_active=True).only("id").first()
    if not perm:
        return PermissionLevel.NONE

    # Active admin roles for this user
    qs = RolePermission.objects.filter(
        permission_id=perm.id,
        role__is_active=True,
        role__deleted_at__isnull=True,
        deleted_at__isnull=True,
        role__members__user=user,
        role__members__is_active=True,
        role__members__deleted_at__isnull=True,
    ).aggregate(max_level=Max("level"))

    return qs["max_level"] or PermissionLevel.NONE


def has_admin_perm(user, permission_code: str, min_level: int) -> bool:
    """
    True if user's effective level >= min_level.
    """
    return resolve_admin_level(user, permission_code) >= min_level
