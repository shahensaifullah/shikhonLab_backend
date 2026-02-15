from django.db import models
# -----------------------------
# 6) CONTENT BLOCK (flexible)
# -----------------------------
class ContentBlockType(models.TextChoices):
    VIDEO = "video", "Video"
    ANIMATION = "animation", "Animation"
    TEXT = "text", "Text"
    QUIZ = "quiz", "Quiz"
    VISUAL = "visual", "Visual Explanation"
    FILE = "file", "File/Worksheet"
