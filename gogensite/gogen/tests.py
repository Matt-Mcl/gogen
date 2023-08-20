from django.test import TestCase
from django.contrib.auth.models import User
from gogen.models import *
import psycopg
from django.conf import settings


class PostgresTestCase(TestCase):
    test_puzzle_type = "uber"
    test_puzzle_date = "20190120"

    def test_can_get_puzzle_from_db(self):
        url = f"http://www.puzzles.grosse.is-a-geek.com/images/gog/puz/{self.test_puzzle_type}/{self.test_puzzle_type}{self.test_puzzle_date}puz.png"

        # Pull the puzzle from the database
        with psycopg.connect(settings.PG_CONNECTION) as conn:
            with conn.cursor() as cur:
                cur.execute(f"SELECT * FROM {self.test_puzzle_type} WHERE puzzle_url = '{url}';")

                puzzle = cur.fetchone()

                name = puzzle[0]
                puz_url = puzzle[1]
                sol_url = puzzle[2]
                words = puzzle[3]
                board = puzzle[4]
                solution_board = puzzle[5]
        
        self.assertEqual(name, "uber20190120")
        self.assertEqual(puz_url, "http://www.puzzles.grosse.is-a-geek.com/images/gog/puz/uber/uber20190120puz.png")
        self.assertEqual(sol_url, "http://www.puzzles.grosse.is-a-geek.com/images/gog/puz/uber/uber20190120sol.png")
        self.assertEqual(words, ["BEGAN", "DOXIE", "FETUS", "GAMP", "GAMY", "GLUED", "GYBED", "GYRO", "JAY", "KUDO", "RHODIC", "ROW", "VIED"])
        self.assertEqual(board, [['V', '', 'X', '', 'W'], ['', '', '', '', ''], ['T', '', 'D', '', 'J'], ['', '', '', '', ''], ['S', '', 'Q', '', 'P']])
        self.assertEqual(solution_board, [['V', 'C', 'X', 'H', 'W'], ['F', 'I', 'B', 'O', 'R'], ['T', 'E', 'D', 'Y', 'J'], ['K', 'U', 'G', 'A', 'M'], ['S', 'L', 'Q', 'N', 'P']])


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
            notes='test notes with more'
        )

        self.assertEqual(user_puzzle_log[0].board, [['V', 'C', 'X', 'H', 'W'], ['F', 'I', 'B', 'O', 'R'], ['T', 'E', 'D', 'Y', 'J'], ['K', 'U', 'G', 'A', 'M'], ['S', 'L', 'Q', 'N', 'P']])
        self.assertEqual(user_puzzle_log[0].placeholders, [['', '', '', '', ''], ['', '', '', '', ''], ['', '', '', '', ''], ['', '', '', '', ''], ['', '', '', '', '']])
        self.assertEqual(user_puzzle_log[0].status, 'C')
        self.assertEqual(user_puzzle_log[0].notes, 'test notes with more')
