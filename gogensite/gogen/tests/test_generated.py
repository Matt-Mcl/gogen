from datetime import timedelta
from urllib.parse import urlencode

import psycopg
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, TestCase
from django.urls import resolve

from gogen.helpers import views_helper

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
        for path in ["/uber1", "/ultra42", "/hyper9999999", "/uber123456789"]:
            self.assertEqual(resolve(path).url_name, "generated_puzzle_view")

    def test_archive_urls_route_to_the_archive_view(self):
        """Dates sit behind _archive, so a seed can never be mistaken for one."""
        for path in ["/uber_archive20190120", "/ultra_archive20190120", "/hyper_archive20190120"]:
            self.assertEqual(resolve(path).url_name, "puzzle_view")

    def test_difficulty_urls_route_to_the_switcher(self):
        for path in ["/uber", "/ultra", "/hyper"]:
            self.assertEqual(resolve(path).url_name, "difficulty_view")

    def test_the_puzzle_lists_are_gone(self):
        with self.assertRaises(Exception):
            resolve("/puzzlelist/uber")

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

    def test_missing_seed_redirects_to_the_earliest_incomplete(self):
        """A seed that was never generated is a soft landing, not a 404."""
        response = self.client.get(f"/{self.PUZZLE_TYPE}999999999")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], f"/{self.PUZZLE_TYPE}1")

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


def make_request(user=None):
    """A bare request carrying just the user, for the helpers that need one."""
    request = RequestFactory().get("/")
    request.user = user or AnonymousUser()

    return request


class DifficultySwitcherTestCase(TestCase):
    """/uber, /ultra and /hyper jump to the earliest puzzle not yet solved."""

    def setUp(self):
        self.seeds = views_helper.generated_seeds("uber")
        if not self.seeds:
            self.skipTest("No generated uber puzzles stored; run gogenmaker/save_puzzles.py")

        self.user = User.objects.create_user(username="testuser", password="testpassword")

    def complete(self, seeds):
        PuzzleLog.objects.bulk_create([
            PuzzleLog(puzzle_type="uber_generated", puzzle_date=str(seed), status="C",
                      board=[], placeholders=[], notes="", user=self.user)
            for seed in seeds
        ])

    def test_starts_at_the_first_puzzle(self):
        response = self.client.get("/uber")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], f"/uber{self.seeds[0]}")

    def test_skips_puzzles_already_solved(self):
        self.client.login(username="testuser", password="testpassword")
        self.complete(self.seeds[:3])

        response = self.client.get("/uber")

        self.assertEqual(response["Location"], f"/uber{self.seeds[3]}")

    def test_an_unfinished_puzzle_is_not_skipped(self):
        """Only completions count, so a half-done puzzle is still offered."""
        self.client.login(username="testuser", password="testpassword")
        PuzzleLog.objects.create(puzzle_type="uber_generated", puzzle_date=str(self.seeds[0]),
                                 status="I", board=[], placeholders=[], notes="", user=self.user)

        response = self.client.get("/uber")

        self.assertEqual(response["Location"], f"/uber{self.seeds[0]}")

    def test_solving_everything_lands_on_the_last_puzzle(self):
        """Running out must not dead-end the user."""
        self.client.login(username="testuser", password="testpassword")
        self.complete(self.seeds)

        response = self.client.get("/uber")

        self.assertEqual(response["Location"], f"/uber{self.seeds[-1]}")

    def test_a_type_with_no_puzzles_does_not_crash(self):
        request = make_request(self.user)

        self.assertIsNone(views_helper.earliest_incomplete_seed(request, "nosuchtype"))


class DailyPuzzleTestCase(TestCase):
    """The home page walks the generated uber seeds, one per day."""

    def setUp(self):
        self.seed = views_helper.daily_seed()
        if not views_helper.generated_seeds("uber"):
            self.skipTest("No generated uber puzzles stored; run gogenmaker/save_puzzles.py")

    def test_seed_advances_one_per_day(self):
        self.assertEqual(views_helper.daily_seed(views_helper.DAILY_EPOCH), 1)
        self.assertEqual(views_helper.daily_seed(views_helper.DAILY_EPOCH + timedelta(days=4)), 5)

    def test_seed_never_precedes_the_first_puzzle(self):
        before = views_helper.DAILY_EPOCH - timedelta(days=30)

        self.assertEqual(views_helper.daily_seed(before), 1)

    def test_home_page_serves_todays_puzzle(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Daily Uber")
        self.assertContains(response, f'name="url" value="/uber{self.seed}"')

    def test_banner_counts_every_generated_puzzle(self):
        """Logged out, the pitch is the generated library, not the archive."""
        total = sum(len(views_helper.generated_seeds(t)) for t in views_helper.GENERATED_TYPES)

        response = self.client.get("/")

        self.assertContains(response, f"unlock all {total:,} puzzles")


class NextButtonTestCase(TestCase):
    """Next resumes unfinished work on the daily, and skips forward elsewhere."""

    def setUp(self):
        self.seeds = views_helper.generated_seeds("uber")
        if len(self.seeds) < 3:
            self.skipTest("Not enough generated uber puzzles stored")

        self.user = User.objects.create_user(username="testuser", password="testpassword")

    def next_url(self, seed, is_daily=False, user=None):
        return views_helper.get_next_generated_url(make_request(user), "uber", seed, is_daily)

    def test_logged_out_users_get_no_next(self):
        self.assertIsNone(self.next_url(self.seeds[0]))
        self.assertIsNone(self.next_url(self.seeds[0], is_daily=True))

    def test_daily_next_goes_back_to_the_earliest_unsolved(self):
        """On the daily, Next picks up whatever was left behind."""
        self.assertEqual(self.next_url(self.seeds[4], is_daily=True, user=self.user),
                         f"/uber{self.seeds[0]}")

    def test_next_steps_forward_off_the_daily(self):
        """Elsewhere Next moves on, so a puzzle can be skipped unsolved."""
        self.assertEqual(self.next_url(self.seeds[0], user=self.user), f"/uber{self.seeds[1]}")

    def test_next_falls_back_when_there_is_nothing_after(self):
        self.assertEqual(self.next_url(self.seeds[-1], user=self.user), f"/uber{self.seeds[0]}")

    def test_next_is_disabled_when_it_would_link_to_itself(self):
        """Caught up on the daily: there is nowhere left to send them."""
        PuzzleLog.objects.bulk_create([
            PuzzleLog(puzzle_type="uber_generated", puzzle_date=str(seed), status="C",
                      board=[], placeholders=[], notes="", user=self.user)
            for seed in self.seeds[:-1]
        ])

        self.assertIsNone(self.next_url(self.seeds[-1], is_daily=True, user=self.user))


class LeaderboardCountsTestCase(TestCase):
    """Archive and generated completions are counted together."""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpassword")
        self.client.login(username="testuser", password="testpassword")

    def log(self, puzzle_type, puzzle_date, status="C"):
        PuzzleLog.objects.create(puzzle_type=puzzle_type, puzzle_date=puzzle_date, status=status,
                                 board=[], placeholders=[], notes="", user=self.user)

    def test_columns_combine_both_sources_and_sum_to_the_total(self):
        self.log("uber", "20190120")
        self.log("uber_generated", "1")
        self.log("ultra_generated", "2")
        self.log("hyper", "20190121")
        self.log("uber_generated", "3", status="I")   # unfinished, must not count

        # The navbar links to /leaderboard, which APPEND_SLASH redirects
        response = self.client.get("/leaderboard", follow=True)
        row = [user for user in response.context["users_and_scores"] if user[0] == "testuser"][0]

        self.assertEqual(row[1:], (2, 1, 1, 4))
