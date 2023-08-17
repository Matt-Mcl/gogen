from django.apps import AppConfig


class GogenConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'gogen'

    def ready(self):
        from .models import PuzzleLog
        puzzle_logs = PuzzleLog.objects.filter(status=PuzzleLog.STATUS_CHOICES[1][0])

        for pl in puzzle_logs:
            # If any placeholders are filled, continue
            if not all(all(element == '' for element in row) for row in pl.placeholders):
                continue
            # If any letters have * next to them, continue
            elif any(any(len(element) == 2 for element in row) for row in pl.board):
                continue
                
            # If unedited, delete record to save space
            pl.delete()
