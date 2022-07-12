from django.contrib import admin

from .models import PuzzleLog

@admin.register(PuzzleLog)
class PuzzleLogAdmin(admin.ModelAdmin):
    list_display = [field.name for field in PuzzleLog._meta.get_fields()]
