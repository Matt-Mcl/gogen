from urllib.parse import urlencode

import psycopg
from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import resolve

from gogen.models import *


def fetch_generated(seed):
    """Read a generated puzzle straight from the puzzle database."""
    try:
        with psycopg.connect(settings.PG_CONNECTION) as conn:
            return conn.execute(
                "SELECT puzzle_board, solution_board, words FROM uber_generated WHERE puzzle_name = %s;",
                (f"uber{seed}",),
            ).fetchone()
    except psycopg.errors.UndefinedTable:
        return None


class GeneratedPuzzleRoutingTestCase(TestCase):

    def test_seed_urls_route_to_the_generated_view(self):
        for path in ["/uber1", "/uber42", "/uber9999999"]:
            self.assertEqual(resolve(path).url_name, "generated_puzzle_view")

    def test_dated_urls_still_route_to_the_archive_view(self):
        """A seed can never swallow a date, because seeds stop at seven digits."""
        self.assertEqual(resolve("/uber20190120").url_name, "puzzle_view")

    def test_seed_zero_is_not_a_puzzle(self):
        with self.assertRaises(Exception):
            resolve("/uber0")


class GeneratedPuzzleTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.puzzle = fetch_generated(1)

    def setUp(self):
        if self.puzzle is None:
            self.skipTest("No generated puzzles stored; run gogenmaker/save_puzzles.py")

        self.puzzle_board, self.solution_board, self.words = self.puzzle
        self.user = User.objects.create_user(username="testuser", password="testpassword")

    def submit(self, board):
        """Post `board` in the same field order the puzzle form uses."""
        data = [("url", "/uber1")]
        for row in range(5):
            for col in range(5):
                # Given cells are not inputs, so the form never posts them back
                if not self.puzzle_board[row][col]:
                    data.append((f"{row}{col}_board_letter", board[row][col]))

        data += [("submit_button", ""), ("notes", "test notes"),
                 ("placeholders", ",".join([""] * 25))]

        return self.client.post("/uber1", urlencode(data),
                                content_type="application/x-www-form-urlencoded")

    def wrong_board(self):
        board = [row[:] for row in self.solution_board]
        board[1][1] = "A" if board[1][1] != "A" else "B"
        return board

    def test_shows_the_puzzle(self):
        response = self.client.get("/uber1")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Generated Uber 1")
        for word in self.words:
            self.assertContains(response, word)

    def test_missing_seed_is_not_found(self):
        self.assertEqual(self.client.get("/uber9999999").status_code, 404)

    def test_correct_solution_is_accepted(self):
        response = self.submit(self.solution_board)

        self.assertContains(response, "Correct!")
        self.assertNotContains(response, "Incorrect!")

    def test_wrong_solution_is_rejected(self):
        response = self.submit(self.wrong_board())

        self.assertContains(response, "Incorrect!")

    def test_completion_is_logged_against_the_seed(self):
        self.client.login(username="testuser", password="testpassword")
        self.submit(self.solution_board)

        log = PuzzleLog.objects.get(user=self.user, puzzle_type="uber_generated", puzzle_date="1")
        self.assertEqual(log.status, "C")
        self.assertEqual(log.board, self.solution_board)

    def test_wrong_answer_is_logged_as_incomplete(self):
        self.client.login(username="testuser", password="testpassword")
        self.submit(self.wrong_board())

        log = PuzzleLog.objects.get(user=self.user, puzzle_type="uber_generated", puzzle_date="1")
        self.assertEqual(log.status, "I")

    def test_a_solved_puzzle_stays_solved(self):
        self.client.login(username="testuser", password="testpassword")
        self.submit(self.solution_board)

        response = self.submit(self.wrong_board())

        self.assertContains(response, "Correct!")
        log = PuzzleLog.objects.get(user=self.user, puzzle_type="uber_generated", puzzle_date="1")
        self.assertEqual(log.status, "C")

    def test_progress_is_restored(self):
        self.client.login(username="testuser", password="testpassword")
        self.submit(self.wrong_board())

        response = self.client.get("/uber1")
        self.assertContains(response, "test notes")

    def test_generated_logs_do_not_mix_with_archive_logs(self):
        """The seed lives in puzzle_date, so it must not collide with a date."""
        self.client.login(username="testuser", password="testpassword")
        self.submit(self.solution_board)

        self.assertEqual(PuzzleLog.objects.filter(puzzle_type="uber").count(), 0)
