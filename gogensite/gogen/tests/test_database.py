from gogen.models import *
from django.test import TestCase
from ..helpers import test_helper


class PostgresTestCase(TestCase):
    test_puzzle_type = "uber"
    test_puzzle_date = "20190120"

    def test_can_get_puzzle_from_db(self):
        puzzle = test_helper.get_puzzle(self.test_puzzle_type, self.test_puzzle_date)

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

    #TODO: add test for ultra and hyper for completeness
