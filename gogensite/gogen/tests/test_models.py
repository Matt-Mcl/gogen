from gogen.models import *
from django.test import TransactionTestCase
from django.contrib.auth.models import User
from django.db.utils import DataError, IntegrityError
from django.core.exceptions import ValidationError

class PuzzleLogTestCase(TransactionTestCase):

    def setUp(self):
        self.test_puzzle_type = "uber"
        self.test_puzzle_date = "20190120"
        self.test_status = "I"
        self.test_board = [['V', '*', 'X', 'H', 'W'], ['*', 'I', 'B', 'O', 'R'], ['T', 'E', 'D', 'Y', 'J'], ['K', 'U', 'G', 'A', 'M'], ['S', 'L', 'Q', 'N', 'P']]
        self.test_placeholders = [['A', 'B', '', '', ''], ['', 'C', '', 'D', ''], ['', '', 'E', '', ''], ['', '', 'F', '', ''], ['', '', 'G', '', '']]
        self.test_notes = "test notes"
        self.test_user = User.objects.create(username="testuser", password="testpassword")
        PuzzleLog.objects.create(
            puzzle_type=self.test_puzzle_type,
            puzzle_date=self.test_puzzle_date,
            status=self.test_status,
            board=self.test_board, 
            placeholders=self.test_placeholders,
            notes=self.test_notes,
            user=self.test_user
        )

    def test_can_complete_puzzle(self):
        user_puzzle_log_qd = PuzzleLog.objects.filter(puzzle_type=self.test_puzzle_type, puzzle_date=self.test_puzzle_date, user=self.test_user)

        user_puzzle_log_qd.update(
            board=[['V', 'C', 'X', 'H', 'W'], ['F', 'I', 'B', 'O', 'R'], ['T', 'E', 'D', 'Y', 'J'], ['K', 'U', 'G', 'A', 'M'], ['S', 'L', 'Q', 'N', 'P']], 
            placeholders = [['', '', '', '', ''], ['', '', '', '', ''], ['', '', '', '', ''], ['', '', '', '', ''], ['', '', '', '', '']],
            status='C',
            notes="test notes with more"
        )

        user_puzzle_log = user_puzzle_log_qd[0]

        self.assertEqual(user_puzzle_log.board, [['V', 'C', 'X', 'H', 'W'], ['F', 'I', 'B', 'O', 'R'], ['T', 'E', 'D', 'Y', 'J'], ['K', 'U', 'G', 'A', 'M'], ['S', 'L', 'Q', 'N', 'P']])
        self.assertEqual(user_puzzle_log.placeholders, [['', '', '', '', ''], ['', '', '', '', ''], ['', '', '', '', ''], ['', '', '', '', ''], ['', '', '', '', '']])
        self.assertEqual(user_puzzle_log.status, 'C')
        self.assertEqual(user_puzzle_log.notes, "test notes with more")

    def test_cannot_save_invalid_puzzle(self):
        user_puzzle_log_qd = PuzzleLog.objects.filter(puzzle_type=self.test_puzzle_type, puzzle_date=self.test_puzzle_date, user=self.test_user)

        self.assertRaises(DataError, user_puzzle_log_qd.update, puzzle_type = "A" * 256)
        self.assertRaises(DataError, user_puzzle_log_qd.update, puzzle_date = "A" * 256)
        self.assertRaises(DataError, user_puzzle_log_qd.update, status = "Invalid Status")
        self.assertRaises(DataError, user_puzzle_log_qd.update, notes = "A" * 1025)
        self.assertRaises(IntegrityError, user_puzzle_log_qd.update, user = "")


class SettingsTestCase(TransactionTestCase):

    def setUp(self):
        self.test_user = User.objects.create(username="testuser", password="testpassword")
        self.notes_template = NoteTemplate.objects.create(
            name="test template",
            template="test template",
        )
    
    def test_settings_can_be_created(self):
        Settings.objects.create(user=self.test_user)
        self.assertEqual(Settings.objects.count(), 1)
    
    def test_settings_cannot_be_created_without_user(self):
        self.assertRaises(IntegrityError, Settings.objects.create)
    
    def test_settings_can_be_updated(self):
        settings = Settings.objects.create(user=self.test_user)
        settings.notes_enabled = False
        settings.preset_notes = self.notes_template
        settings.save()
        self.assertEqual(settings.notes_enabled, False)
        self.assertEqual(settings.preset_notes, self.notes_template)
    
    def test_settings_cannot_be_updated_with_invalid_values(self):
        Settings.objects.create(user=self.test_user)
        settings_qd = Settings.objects.filter(user=self.test_user)
        self.assertRaises(ValidationError, settings_qd.update, notes_enabled = "Invalid")
        self.assertRaises(ValueError, settings_qd.update, preset_notes = "Invalid")

    def test_settings_default_values(self):
        settings = Settings.objects.create(user=self.test_user)
        self.assertEqual(settings.notes_enabled, True)
        self.assertEqual(settings.preset_notes, None)
    


class NoteTemplateCase(TransactionTestCase):

    def test_note_template_can_be_created(self):
        NoteTemplate.objects.create(
            name="test template",
            template="test template",
        )
        self.assertEqual(NoteTemplate.objects.count(), 1)

    def test_note_template_can_be_updated(self):
        note_template = NoteTemplate.objects.create(
            name="test template",
            template="test template",
        )
        note_template.name = "updated name"
        note_template.template = "updated template"
        note_template.save()
        self.assertEqual(note_template.name, "updated name")
        self.assertEqual(note_template.template, "updated template")

    def test_note_template_cannot_be_created_with_invalid_values(self):
        self.assertRaises(DataError, NoteTemplate.objects.create, name="A" * 256)
        self.assertRaises(DataError, NoteTemplate.objects.create, template="A" * 1025)
