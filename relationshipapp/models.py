from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

from sharedapp.models import TimeStampedSoftDeleteModel

User = get_user_model()

class GuardianRelationshipStatus(models.TextChoices):
    """
    Status lifecycle of parent-student relationship.
    """
    PENDING = "pending", "Pending"  # Request created, waiting approval
    ACTIVE = "active", "Active"  # Approved → parent can monitor student
    REJECTED = "rejected", "Rejected"  # Explicitly declined
    REVOKED = "revoked", "Revoked"  # Previously active but removed later


class GuardianRelationship(TimeStampedSoftDeleteModel):
    """
    Bridge table between Parent and Student users.

    RELATIONSHIP TYPE:
        User (Parent)  ----< GuardianRelationship >----  User (Student)

    This is NOT a simple ManyToMany.
    It is an explicit relationship model because:

        • We need request/approval flow
        • We need status tracking
        • We need permission flags
        • We need audit timestamps
        • We need per-parent permission control

    TABLE RELATIONSHIP SUMMARY:

        accounts_user (parent)
            ↓ FK
        guardian_relationship
            ↑ FK
        accounts_user (student)

    """

    # -----------------------------
    # Foreign Keys
    # -----------------------------

    parent = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="child_links",
        help_text="User with parent role"
    )
    """
    References accounts_user table.
    This user must have role = PARENT.

    Reverse relation:
        parent.child_links.all()
        → gives all students linked to this parent
    """

    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="guardian_links",
        help_text="User with student role"
    )
    """
    References accounts_user table.
    This user must have role = STUDENT.

    Reverse relation:
        student.guardian_links.all()
        → gives all parents linked to this student
    """

    # -----------------------------
    # Relationship State
    # -----------------------------

    status = models.CharField(
        max_length=20,
        choices=GuardianRelationshipStatus.choices,
        default=GuardianRelationshipStatus.PENDING,
        db_index=True,
    )
    """
    Controls whether monitoring is active.

    PENDING → waiting for approval
    ACTIVE → parent has access
    REJECTED → declined request
    REVOKED → removed after being active
    """

    # -----------------------------
    # Audit & Consent Tracking
    # -----------------------------

    requested_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="guardian_requests_made",
    )
    """
    Who initiated the relationship.

    Can be:
        • Parent
        • Student

    Useful for audit logs and UI logic.
    """

    requested_at = models.DateTimeField(default=timezone.now)
    responded_at = models.DateTimeField(null=True, blank=True)

    """
    requested_at → when request was created
    responded_at → when accepted/rejected
    """

    # -----------------------------
    # Monitoring Permissions
    # -----------------------------

    can_view_progress = models.BooleanField(default=True)
    can_receive_reports = models.BooleanField(default=True)
    can_view_assessments = models.BooleanField(default=True)

    """
    These permissions are PER relationship.
    That means:

        Parent A may see full reports.
        Parent B may see summary only.

    This design scales much better than global flags.
    """

    # -----------------------------
    # Optional Metadata
    # -----------------------------

    relation_label = models.CharField(max_length=40, blank=True)
    """
    Example:
        "Father"
        "Mother"
        "Guardian"
        "Uncle"
    """

    # -----------------------------
    # DB Constraints & Indexing
    # -----------------------------

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["parent", "student"],
                name="uniq_parent_student_link"
            )
        ]
        indexes = [
            models.Index(fields=["parent", "status"]),
            models.Index(fields=["student", "status"]),
        ]

    def __str__(self):
        return f"{self.parent_id} -> {self.student_id} ({self.status})"