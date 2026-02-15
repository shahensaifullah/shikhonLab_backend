# core/models.py
from django.db import models
from django.utils import timezone


class SoftDeleteQuerySet(models.QuerySet):
    def soft_delete(self):
        return super().update(deleted_at=timezone.now())

    def hard_delete(self):
        return super().delete()

    def alive(self):
        return self.filter(deleted_at__isnull=True)

    def dead(self):
        return self.filter(deleted_at__isnull=False)


class SoftDeleteManager(models.Manager):
    """
    Default manager: hides soft-deleted rows.
    """
    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db).alive()

    # Optional convenience pass-throughs
    def dead(self):
        return SoftDeleteQuerySet(self.model, using=self._db).dead()

    def hard_delete(self):
        return self.get_queryset().hard_delete()


class AllObjectsManager(models.Manager):
    """
    Includes deleted rows (use for admin/restore/audit).
    """
    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db)

    def alive(self):
        return self.get_queryset().alive()

    def dead(self):
        return self.get_queryset().dead()


