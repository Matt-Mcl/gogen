from gogen.models import *
from django.test import TestCase
from django.contrib.auth.models import User


class PuzzleLogTestCase(TestCase):

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
        user_puzzle_log = PuzzleLog.objects.filter(puzzle_type=self.test_puzzle_type, puzzle_date=self.test_puzzle_date, user=self.test_user)

        user_puzzle_log.update(
            board=[['V', 'C', 'X', 'H', 'W'], ['F', 'I', 'B', 'O', 'R'], ['T', 'E', 'D', 'Y', 'J'], ['K', 'U', 'G', 'A', 'M'], ['S', 'L', 'Q', 'N', 'P']], 
            placeholders = [['', '', '', '', ''], ['', '', '', '', ''], ['', '', '', '', ''], ['', '', '', '', ''], ['', '', '', '', '']],
            status='C',
            notes="test notes with more"
        )

        self.assertEqual(user_puzzle_log[0].board, [['V', 'C', 'X', 'H', 'W'], ['F', 'I', 'B', 'O', 'R'], ['T', 'E', 'D', 'Y', 'J'], ['K', 'U', 'G', 'A', 'M'], ['S', 'L', 'Q', 'N', 'P']])
        self.assertEqual(user_puzzle_log[0].placeholders, [['', '', '', '', ''], ['', '', '', '', ''], ['', '', '', '', ''], ['', '', '', '', ''], ['', '', '', '', '']])
        self.assertEqual(user_puzzle_log[0].status, 'C')
        self.assertEqual(user_puzzle_log[0].notes, "test notes with more")

    # TODO: test that puzzle log can be created and invalid can't


class SettingsTestCase(TestCase):

    # test that settings can be created and invalid can't
    # test that settings can be attached to a user
    # test that default values are correctly populated
    # test that settings can be updated
    pass


class NoteTemplateCase(TestCase):

    # test that note template can be created and invalid can't
    # test that note template can be updated
    pass
