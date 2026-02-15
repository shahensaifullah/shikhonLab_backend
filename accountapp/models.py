# accounts/models.py
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from pictures.models import PictureField

from sharedapp.managers import AllObjectsManager, SoftDeleteManager
from sharedapp.models import TimeStampedSoftDeleteModel
from .managers import UserManager


class User(TimeStampedSoftDeleteModel, AbstractBaseUser, PermissionsMixin):
    phone = models.CharField(max_length=20, unique=True, db_index=True)
    email = models.EmailField(blank=True, null=True)

    full_name = models.CharField(max_length=120, blank=True)
    avatar = PictureField(
        upload_to="avatars",
        aspect_ratios=[None, "1/1", "3/2", "16/9"],
        width_field="picture_width",
        height_field="picture_height",
    )
    picture_width = models.PositiveIntegerField(editable=False)
    picture_height = models.PositiveIntegerField(editable=False)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = []

    # IMPORTANT:
    # 1) Django needs BaseUserManager methods here (create_user/superuser)
    # 2) We also want soft-delete filtering by default
    #
    # So we attach BOTH:
    base_objects = UserManager()      # for creates (Django uses this)
    objects = SoftDeleteManager()     # alive only
    all_objects = AllObjectsManager() # includes deleted

    def __str__(self):
        return self.full_name or self.phone


class Role(models.TextChoices):
    STUDENT = "student", "Student"
    PARENT = "parent", "Parent"
    TEACHER = "teacher", "Teacher"
    ADMIN = "admin", "Admin"


class UserRole(TimeStampedSoftDeleteModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="roles")
    role = models.CharField(max_length=20, choices=Role.choices)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "role"], name="uniq_user_role")
        ]
        indexes = [
            models.Index(fields=["role"]),
            models.Index(fields=["user", "role"]),
        ]


class StudentProfile(TimeStampedSoftDeleteModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="student_profile")

    current_grade_label = models.CharField(max_length=40, blank=True)  # temp; later connect to Grade table
    date_of_birth = models.DateField(blank=True, null=True)
    school_name = models.CharField(max_length=160, blank=True)


class ParentProfile(TimeStampedSoftDeleteModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="parent_profile")

    occupation = models.CharField(max_length=120, blank=True)
    address_text = models.CharField(max_length=255, blank=True)


class TeacherProfile(TimeStampedSoftDeleteModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="teacher_profile")

    bio = models.TextField(blank=True)
    expertise = models.CharField(max_length=255, blank=True)
