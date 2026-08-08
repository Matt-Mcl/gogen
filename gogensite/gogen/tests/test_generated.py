from urllib.parse import urlencode

import psycopg
from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import resolve

from gogen.models import *


def fetch_generated(puzzle_type, seed):
    """Read a generated puzzle straight from the puzzle database."""
    try:
        with psycopg.connect(settings.PG_CONNECTION) as conn:
            return conn.execute(
                f"SELECT puzzle_board, solution_board, words FROM {puzzle_type}_generated "
                "WHERE puzzle_name = %s;",
                (f"{puzzle_type}{seed}",),
            ).fetchone()
    except psycopg.errors.UndefinedTable:
        return None


class GeneratedPuzzleRoutingTestCase(TestCase):

    def test_seed_urls_route_to_the_generated_view(self):
        for path in ["/uber1", "/ultra42", "/hyper9999999"]:
            self.assertEqual(resolve(path).url_name, "generated_puzzle_view")

    def test_dated_urls_still_route_to_the_archive_view(self):
        """A seed can never swallow a date, because seeds stop at seven digits."""
        for path in ["/uber20190120", "/ultra20190120", "/hyper20190120"]:
            self.assertEqual(resolve(path).url_name, "puzzle_view")

    def test_seed_zero_is_not_a_puzzle(self):
        with self.assertRaises(Exception):
            resolve("/uber0")


class GeneratedPuzzleTests:
    """Shared checks, run against each generated puzzle type.

    Not a TestCase itself, so these only run through the subclasses below.
    """

    PUZZLE_TYPE = None
    SEED = 1

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.puzzle = fetch_generated(cls.PUZZLE_TYPE, cls.SEED)

    def setUp(self):
        if self.puzzle is None:
            self.skipTest(f"No generated {self.PUZZLE_TYPE} puzzles stored; "
                          "run gogenmaker/save_puzzles.py")

        self.puzzle_board, self.solution_board, self.words = self.puzzle
        self.url = f"/{self.PUZZLE_TYPE}{self.SEED}"
        self.log_type = f"{self.PUZZLE_TYPE}_generated"
        self.user = User.objects.create_user(username="testuser", password="testpassword")

    def log(self):
        return PuzzleLog.objects.get(user=self.user, puzzle_type=self.log_type,
                                     puzzle_date=str(self.SEED))

    def submit(self, board):
        """Post `board` in the same field order the puzzle form uses."""
        data = [("url", self.url)]
        for row in range(5):
            for col in range(5):
                # Given cells are not inputs, so the form never posts them back
                if not self.puzzle_board[row][col]:
                    data.append((f"{row}{col}_board_letter", board[row][col]))

        data += [("submit_button", ""), ("notes", "test notes"),
                 ("placeholders", ",".join([""] * 25))]

        return self.client.post(self.url, urlencode(data),
                                content_type="application/x-www-form-urlencoded")

    def wrong_board(self):
        board = [row[:] for row in self.solution_board]
        # Change a cell that is not given away, so it is actually posted back
        for row in range(5):
            for col in range(5):
                if not self.puzzle_board[row][col]:
                    board[row][col] = "A" if board[row][col] != "A" else "B"
                    return board
        raise AssertionError("every cell is a clue")

    def test_shows_the_puzzle(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f"Generated {self.PUZZLE_TYPE.capitalize()} {self.SEED}")
        for word in self.words:
            self.assertContains(response, word)

    def test_missing_seed_is_not_found(self):
        self.assertEqual(self.client.get(f"/{self.PUZZLE_TYPE}9999999").status_code, 404)

    def test_correct_solution_is_accepted(self):
        response = self.submit(self.solution_board)

        self.assertContains(response, "Correct!")
        self.assertNotContains(response, "Incorrect!")

    def test_wrong_solution_is_rejected(self):
        self.assertContains(self.submit(self.wrong_board()), "Incorrect!")

    def test_completion_is_logged_against_the_seed(self):
        self.client.login(username="testuser", password="testpassword")
        self.submit(self.solution_board)

        self.assertEqual(self.log().status, "C")
        self.assertEqual(self.log().board, self.solution_board)

    def test_wrong_answer_is_logged_as_incomplete(self):
        self.client.login(username="testuser", password="testpassword")
        self.submit(self.wrong_board())

        self.assertEqual(self.log().status, "I")

    def test_a_solved_puzzle_stays_solved(self):
        self.client.login(username="testuser", password="testpassword")
        self.submit(self.solution_board)

        response = self.submit(self.wrong_board())

        self.assertContains(response, "Correct!")
        self.assertEqual(self.log().status, "C")

    def test_progress_is_restored(self):
        self.client.login(username="testuser", password="testpassword")
        self.submit(self.wrong_board())

        self.assertContains(self.client.get(self.url), "test notes")

    def test_generated_logs_do_not_mix_with_archive_logs(self):
        """The seed lives in puzzle_date, so it must not collide with a date."""
        self.client.login(username="testuser", password="testpassword")
        self.submit(self.solution_board)

        self.assertEqual(PuzzleLog.objects.filter(puzzle_type=self.PUZZLE_TYPE).count(), 0)


class GeneratedUberTestCase(GeneratedPuzzleTests, TestCase):
    PUZZLE_TYPE = "uber"


class GeneratedUltraTestCase(GeneratedPuzzleTests, TestCase):
    PUZZLE_TYPE = "ultra"


class GeneratedHyperTestCase(GeneratedPuzzleTests, TestCase):
    PUZZLE_TYPE = "hyper"
