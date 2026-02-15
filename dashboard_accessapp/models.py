from django.contrib.auth import get_user_model
from django.db import models

from dashboard_accessapp.enums import PermissionLevel
from sharedapp.models import TimeStampedSoftDeleteModel

User = get_user_model()




class AdminPermission(TimeStampedSoftDeleteModel):
    """
    A single capability in the admin dashboard.

    Example codes:
      - content.course
      - content.lesson
      - content.publish
      - users.view
      - enrollments.manage
      - purchases.view
      - purchases.refund
      - admin.roles (manage roles & admin members)
    """
    code = models.CharField(max_length=80, unique=True, db_index=True)
    name = models.CharField(max_length=120)
    description = models.CharField(max_length=255, blank=True)

    is_active = models.BooleanField(default=True, db_index=True)

    def __str__(self):
        return self.code


class AdminRole(TimeStampedSoftDeleteModel):
    """
    Named role like:
      - Super Admin
      - Content Admin
      - Support Admin
      - Finance Admin
    """
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=80, unique=True)

    is_system_role = models.BooleanField(default=False, db_index=True)
    """
    System roles are created by migrations and should not be edited casually.
    Example: Super Admin
    """

    is_active = models.BooleanField(default=True, db_index=True)

    def __str__(self):
        return self.name


class RolePermission(TimeStampedSoftDeleteModel):
    """
    Assigns a permission + level to a role.

    RELATIONSHIP:
        AdminRole 1 ---< RolePermission >--- 1 AdminPermission
    """
    role = models.ForeignKey(AdminRole, on_delete=models.CASCADE, related_name="role_permissions")
    permission = models.ForeignKey(AdminPermission, on_delete=models.CASCADE, related_name="in_roles")

    level = models.PositiveSmallIntegerField(choices=PermissionLevel.choices, default=PermissionLevel.NONE)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["role", "permission"], name="uniq_role_permission")
        ]
        indexes = [
            models.Index(fields=["role"]),
            models.Index(fields=["permission"]),
            models.Index(fields=["role", "level"]),
        ]

    def __str__(self):
        return f"{self.role.slug}:{self.permission.code}={self.level}"


class AdminMembership(TimeStampedSoftDeleteModel):
    """
    Links a User to an AdminRole (dashboard access).

    RELATIONSHIP:
        User 1 ---< AdminMembership >--- 1 AdminRole
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="admin_memberships")
    role = models.ForeignKey(AdminRole, on_delete=models.PROTECT, related_name="members")

    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "role"], name="uniq_user_admin_role")
        ]
        indexes = [
            models.Index(fields=["user", "is_active"]),
            models.Index(fields=["role", "is_active"]),
        ]

    def __str__(self):
        return f"{self.user_id} -> {self.role.slug}"