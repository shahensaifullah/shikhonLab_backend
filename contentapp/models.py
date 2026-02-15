from pictures.models import PictureField

from contentapp.enums import ContentBlockType
from sharedapp.models import TimeStampedSoftDeleteModel


# -----------------------------
# 1) CLASS / GRADE (BD context)
# -----------------------------
from django.db import models
from django.utils.text import slugify



class GradeLevel(TimeStampedSoftDeleteModel):
    """
    BD learning level: Playgroup, Class 1..10, Admission...
    """
    name = models.CharField(max_length=60, unique=True)
    order = models.PositiveIntegerField(default=0, db_index=True)

    def __str__(self):
        return self.name


class Subject(TimeStampedSoftDeleteModel):
    """
    Subject is reusable too (Math, Science...).
    It is NOT tied to a grade anymore.
    """
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=120, unique=True)

    is_active = models.BooleanField(default=True, db_index=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Course(TimeStampedSoftDeleteModel):
    """
    A reusable course package.
    It does NOT belong to any single grade/subject.
    Placement controls where it appears.
    """
    title = models.CharField(max_length=160)
    slug = models.SlugField(max_length=180, unique=True)

    short_description = models.CharField(max_length=255, blank=True)

    cover_image = PictureField(
        upload_to="course_covers",
        aspect_ratios=[None, "1/1", "3/2", "16/9"],
        width_field="picture_width",
        height_field="picture_height",
    )
    picture_width = models.PositiveIntegerField(editable=False)
    picture_height = models.PositiveIntegerField(editable=False)

    # global publish (course exists / not)
    is_active = models.BooleanField(default=True, db_index=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)[:180]
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class CoursePlacement(TimeStampedSoftDeleteModel):
    """
    Maps a Course into a Grade + Subject.

    RELATIONSHIPS:
        GradeLevel 1 ---< CoursePlacement >--- 1 Course
        Subject    1 ---< CoursePlacement
    """
    grade = models.ForeignKey(GradeLevel, on_delete=models.CASCADE, related_name="course_placements")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="course_placements")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="placements")

    # ordering within (grade + subject) page
    order = models.PositiveIntegerField(default=0, db_index=True)

    # publishing can differ per grade/subject
    is_published = models.BooleanField(default=False, db_index=True)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["grade", "subject", "course"], name="uniq_course_placement"),
            models.UniqueConstraint(fields=["grade", "subject", "order"], name="uniq_course_order_per_grade_subject"),
        ]
        indexes = [
            models.Index(fields=["grade", "subject", "is_published", "order"]),
            models.Index(fields=["course"]),
        ]

    def __str__(self):
        return f"{self.grade.name} · {self.subject.name} · {self.course.title}"


# -----------------------------
# 4) MODULE / CHAPTER
# -----------------------------
class Module(TimeStampedSoftDeleteModel):
    """
    A course contains modules (chapters).

    RELATIONSHIPS:
        Course  1 ---< Module
        Module  1 ---< Lesson
    """
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="modules"
    )

    title = models.CharField(max_length=160)
    order = models.PositiveIntegerField(default=0, db_index=True)

    # story-driven progression can be toggled per module if needed
    is_sequential = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["course", "order"], name="uniq_module_order_per_course")
        ]
        indexes = [
            models.Index(fields=["course", "order"]),
        ]

    def __str__(self):
        return f"{self.course.title} · {self.title}"


# -----------------------------
# 5) LESSON
# -----------------------------
class Lesson(TimeStampedSoftDeleteModel):
    """
    The smallest unit in the learning path.

    RELATIONSHIPS:
        Module 1 ---< Lesson
        Lesson 1 ---< ContentBlock (video/quiz/animation/etc.)
    """
    module = models.ForeignKey(
        Module,
        on_delete=models.CASCADE,
        related_name="lessons"
    )

    title = models.CharField(max_length=180)
    order = models.PositiveIntegerField(default=0, db_index=True)

    # helps story-based flow
    lesson_type = models.CharField(
        max_length=30,
        default="standard",
        help_text="e.g. standard, story, practice, revision"
    )

    is_published = models.BooleanField(default=False, db_index=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["module", "order"], name="uniq_lesson_order_per_module")
        ]
        indexes = [
            models.Index(fields=["module", "is_published", "order"]),
        ]

    def __str__(self):
        return f"{self.module.title} · {self.title}"


class ContentBlock(TimeStampedSoftDeleteModel):
    """
    Flexible building block under a lesson (like Notion blocks).

    Why a single table for different content types?
    - You will add new content formats over time.
    - Keeping one table avoids schema explosion.
    - `data` can store type-specific configuration.

    RELATIONSHIPS:
        Lesson 1 ---< ContentBlock
    """
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name="content_blocks"
    )

    block_type = models.CharField(max_length=20, choices=ContentBlockType.choices, db_index=True)
    order = models.PositiveIntegerField(default=0, db_index=True)

    title = models.CharField(max_length=180, blank=True)

    # type-specific payload (URLs, durations, JSON config, etc.)
    data = models.JSONField(default=dict, blank=True)

    # for rollout/QA
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["lesson", "order"], name="uniq_block_order_per_lesson")
        ]
        indexes = [
            models.Index(fields=["lesson", "is_active", "order"]),
            models.Index(fields=["block_type"]),
        ]

    def __str__(self):
        return f"{self.lesson.title} · {self.block_type} · {self.order}"
