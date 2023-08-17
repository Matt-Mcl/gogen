from django.db import models
from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField
from django.db.models.constraints import UniqueConstraint

class PuzzleLog(models.Model):
    STATUS_CHOICES = [
        ('C', 'Completed'),
        ('I', 'Incomplete')
    ]
    puzzle_type = models.CharField(max_length=255)
    puzzle_date = models.CharField(max_length=255)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES)
    board = ArrayField(
        ArrayField(
            models.CharField(max_length=2, blank=True),
            size=5,
        ),
        size=5,
    )
    placeholders = ArrayField(
        ArrayField(
            models.CharField(max_length=30, blank=True),
            size=5,
        ),
        size=5,
    )
    notes = models.CharField(max_length=1024, blank=True)

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    UniqueConstraint(fields = ['puzzle_type', 'puzzle_date', 'user'], name = 'unique_puzzle_type_and_date_per_user')


class Settings(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    notes_enabled = models.BooleanField(default=True)
