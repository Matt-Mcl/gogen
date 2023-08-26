from gogen.models import *
from django.test import TestCase
from ..helpers import test_helper


class PostgresTestCase(TestCase):

    def setUp(self):
        self.test_puzzle_date = "20190120"

    def test_can_get_uber_from_db(self):
        puzzle = test_helper.get_puzzle("uber", self.test_puzzle_date)

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

    def test_can_get_ultra_from_db(self):
        puzzle = test_helper.get_puzzle("ultra", self.test_puzzle_date)

        name = puzzle[0]
        puz_url = puzzle[1]
        sol_url = puzzle[2]
        words = puzzle[3]
        board = puzzle[4]
        solution_board = puzzle[5]
        
        self.assertEqual(name, "ultra20190120")
        self.assertEqual(puz_url, "http://www.puzzles.grosse.is-a-geek.com/images/gog/puz/ultra/ultra20190120puz.png")
        self.assertEqual(sol_url, "http://www.puzzles.grosse.is-a-geek.com/images/gog/puz/ultra/ultra20190120sol.png")
        self.assertEqual(words, ["BRIT", "COTES", "CYTONS", "DATERS", "FAQIRS", "GYM", "HULA", "JOES", "KITES", "LUXATES", "PLATES", "VOTES", "WON"])
        self.assertEqual(board, [['B', '', 'F', '', 'P'], ['', '', '', '', ''], ['S', '', '', '', 'X'], ['', '', '', '', ''], ['J', '', 'W', '', 'M']])
        self.assertEqual(solution_board, [['B', 'K', 'F', 'D', 'P'],['R', 'I', 'Q', 'A', 'L'],['S', 'E', 'T', 'U', 'X'],['N', 'O', 'C', 'Y', 'H'],['J', 'V', 'W', 'G', 'M']])

    def test_can_get_hyper_from_db(self):
        puzzle = test_helper.get_puzzle("hyper", self.test_puzzle_date)

        name = puzzle[0]
        puz_url = puzzle[1]
        sol_url = puzzle[2]
        words = puzzle[3]
        board = puzzle[4]
        solution_board = puzzle[5]
        
        self.assertEqual(name, "hyper20190120")
        self.assertEqual(puz_url, "http://www.puzzles.grosse.is-a-geek.com/images/gog/puz/hyper/hyper20190120puz.png")
        self.assertEqual(sol_url, "http://www.puzzles.grosse.is-a-geek.com/images/gog/puz/hyper/hyper20190120sol.png")
        self.assertEqual(words, ["WVQ","PGXDCK","MBL","PXFOE","VNS","QTISJAY","UXH","URNEYK","MUFYC","TNOBP"])
        self.assertEqual(board, [['', '', '', '', ''],['', '', '', '', ''],['', '', '', 'F', ''],['', 'N', '', '', ''],['', '', '', '', '']])
        self.assertEqual(solution_board, [['L', 'M', 'P', 'G', 'H'],['W', 'B', 'U', 'X', 'D'],['V', 'R', 'O', 'F', 'C'],['Q', 'N', 'E', 'Y', 'K'],['T', 'I', 'S', 'J', 'A']])
