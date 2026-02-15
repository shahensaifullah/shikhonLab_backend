from django.core.management.base import BaseCommand
from django.utils.text import slugify

from dashboard_accessapp.enums import PermissionLevel
from dashboard_accessapp.models import AdminPermission, AdminRole, RolePermission

PERMISSIONS = [
    ("admin.roles", "Manage Roles & Admin Members", "Create roles, assign/remove admin members"),

    ("content.grade", "Manage Grades", "CRUD grade levels"),
    ("content.subject", "Manage Subjects", "CRUD subjects"),
    ("content.course", "Manage Courses", "CRUD courses"),
    ("content.placement", "Manage Course Placement", "Place courses into grade+subject shelves"),
    ("content.module", "Manage Modules", "CRUD modules"),
    ("content.lesson", "Manage Lessons", "CRUD lessons"),
    ("content.block", "Manage Content Blocks", "CRUD lesson content blocks"),
    ("content.publish", "Publish Content", "Publish/unpublish content"),

    ("users.view", "View Users", "Search and view users"),
    ("relationships.view", "View Parent-Student Links", "View guardian relationships"),
    ("enrollments.manage", "Manage Enrollments", "Grant/revoke/extend enrollments"),

    ("purchases.view", "View Purchases", "View payment and orders"),
    ("purchases.refund", "Refund Purchases", "Issue refunds / reversals"),
]

SYSTEM_ROLES = [
    # role_name, slug, {permission_code: level}
    ("Super Admin", "super-admin", {
        "*": PermissionLevel.ADMIN,
    }),

    ("Content Admin", "content-admin", {
        "content.grade": PermissionLevel.WRITE,
        "content.subject": PermissionLevel.WRITE,
        "content.course": PermissionLevel.WRITE,
        "content.placement": PermissionLevel.WRITE,
        "content.module": PermissionLevel.WRITE,
        "content.lesson": PermissionLevel.WRITE,
        "content.block": PermissionLevel.WRITE,
        "content.publish": PermissionLevel.WRITE,   # set ADMIN if you want strict publishing
    }),

    ("Support Admin", "support-admin", {
        "users.view": PermissionLevel.READ,
        "relationships.view": PermissionLevel.READ,
        "enrollments.manage": PermissionLevel.WRITE,
    }),

    ("Finance Admin", "finance-admin", {
        "purchases.view": PermissionLevel.READ,
        "purchases.refund": PermissionLevel.ADMIN,
    }),
]


class Command(BaseCommand):
    help = "Seed dashboard RBAC: AdminPermission, AdminRole, RolePermission (safe to run multiple times)."

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Seeding permissions..."))
        perm_map = {}

        for code, name, desc in PERMISSIONS:
            perm, _ = AdminPermission.all_objects.get_or_create(
                code=code,
                defaults={"name": name, "description": desc, "is_active": True},
            )
            # if previously soft-deleted, restore
            if perm.deleted_at is not None:
                perm.restore()
            # update basic fields if changed
            changed = False
            if perm.name != name:
                perm.name = name
                changed = True
            if perm.description != desc:
                perm.description = desc
                changed = True
            if perm.is_active is not True:
                perm.is_active = True
                changed = True
            if changed:
                perm.save(update_fields=["name", "description", "is_active", "updated_at"])
            perm_map[code] = perm

        self.stdout.write(self.style.SUCCESS(f"✓ {len(perm_map)} permissions ready."))

        self.stdout.write(self.style.NOTICE("Seeding system roles + role permissions..."))
        all_perm_codes = list(perm_map.keys())

        for role_name, role_slug, policy in SYSTEM_ROLES:
            role, _ = AdminRole.all_objects.get_or_create(
                slug=role_slug,
                defaults={"name": role_name, "is_system_role": True, "is_active": True},
            )
            if role.deleted_at is not None:
                role.restore()

            # keep system roles active + correct name
            update_fields = []
            if role.name != role_name:
                role.name = role_name
                update_fields.append("name")
            if role.is_system_role is not True:
                role.is_system_role = True
                update_fields.append("is_system_role")
            if role.is_active is not True:
                role.is_active = True
                update_fields.append("is_active")
            if update_fields:
                role.save(update_fields=update_fields + ["updated_at"])

            # Apply permissions
            if "*" in policy:
                level = policy["*"]
                target_codes = all_perm_codes
                for code in target_codes:
                    self._upsert_role_perm(role, perm_map[code], level)
            else:
                for code, level in policy.items():
                    if code not in perm_map:
                        self.stdout.write(self.style.WARNING(f"Permission code missing: {code}"))
                        continue
                    self._upsert_role_perm(role, perm_map[code], level)

        self.stdout.write(self.style.SUCCESS("✓ System roles seeded successfully."))

    def _upsert_role_perm(self, role, perm, level):
        rp, _ = RolePermission.all_objects.get_or_create(
            role=role,
            permission=perm,
            defaults={"level": level},
        )
        if rp.deleted_at is not None:
            rp.restore()
        if rp.level != level:
            rp.level = level
            rp.save(update_fields=["level", "updated_at"])
