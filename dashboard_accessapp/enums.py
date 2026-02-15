from django.db import models


class PermissionLevel(models.IntegerChoices):
    """
    Increasing power. Higher includes lower.
    """
    NONE = 0, "None"
    READ = 10, "Read"
    WRITE = 20, "Write"
    ADMIN = 30, "Admin"
