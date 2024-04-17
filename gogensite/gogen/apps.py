from django.apps import AppConfig
import os

class GogenConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'gogen'

    def ready(self):
        if os.getenv("TESTING") == "True":
            return
        
        from .models import PuzzleLog
        incomplete_puzzle_logs = PuzzleLog.objects.filter(status=PuzzleLog.STATUS_CHOICES[1][0])

        for ipl in incomplete_puzzle_logs:
            # If any placeholders are filled, continue
            if not all(all(element == '' for element in row) for row in ipl.placeholders):
                continue
            # If any letters have * next to them, continue
            elif any(any(len(element) == 2 for element in row) for row in ipl.board):
                continue
                
            # If unedited, delete record to save space
            ipl.delete()

        complete_puzzle_logs = PuzzleLog.objects.filter(status=PuzzleLog.STATUS_CHOICES[0][0])

        for cpl in complete_puzzle_logs:
            # clear all placeholders
            cpl.placeholders = [['' for _ in range(5)] for _ in range(5)]
            cpl.save()
