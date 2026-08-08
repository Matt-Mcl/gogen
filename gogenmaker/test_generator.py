"""Tests for the Gogen generator: Uber, Ultra and Hyper.

Run with:  python -m unittest test_generator
"""

import random
import unittest

import generator as g


# Two Uber puzzles taken from the published archive, used to check the solver
# agrees with the real thing: clues plus words must admit exactly one grid.
PUBLISHED = [
    (
        ["BODY", "BOYLA", "CITHRENS", "FUMER", "GOVERNS", "ICY", "JILT",
         "OVERSALT", "QUERNS"],
        [["W", "A", "T", "K", "P"],
         ["S", "H", "L", "I", "C"],
         ["N", "R", "J", "Y", "X"],
         ["Q", "E", "V", "O", "D"],
         ["M", "U", "F", "G", "B"]],
    ),
    (
        ["BASHED", "COPER", "FRY", "KANE", "LOPED", "PREY", "QUOD", "SAWNEY",
         "TISANE", "VOGUISH"],
        [["T", "M", "X", "K", "J"],
         ["Q", "I", "S", "A", "W"],
         ["V", "U", "B", "H", "N"],
         ["G", "O", "P", "E", "F"],
         ["L", "C", "D", "R", "Y"]],
    ),
]


class DictionaryTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.words, cls.rank = g.load_words()

    def test_obeys_the_gogen_rules(self):
        for word in self.words:
            self.assertGreaterEqual(len(word), 3)
            self.assertNotIn("Z", word)
            self.assertEqual(len(set(word)), len(word), f"{word} repeats a letter")
            self.assertTrue(word.isalpha() and word.isupper())

    def test_ranked_most_common_first(self):
        self.assertEqual(self.rank[self.words[0]], 0)
        self.assertLess(self.rank["HOUSE"], self.rank["QADI"])


class AdjacencyTests(unittest.TestCase):

    def test_adjacency_is_a_king_move(self):
        self.assertEqual(len(g.ADJACENT[(0, 0)]), 3)    # corner
        self.assertEqual(len(g.ADJACENT[(0, 2)]), 5)    # edge
        self.assertEqual(len(g.ADJACENT[(2, 2)]), 8)    # middle
        self.assertIn((1, 1), g.ADJACENT[(0, 0)])       # diagonals count

    def test_traceable_follows_the_grid(self):
        grid = PUBLISHED[0][1]
        positions = g.letter_positions(grid)
        self.assertTrue(g.is_traceable("BODY", positions))
        self.assertFalse(g.is_traceable("BOW", positions))

    def test_puzzle_board_shows_only_the_nine_clues(self):
        board = g.puzzle_board(PUBLISHED[0][1])
        given = [(r, c) for r in range(5) for c in range(5) if board[r][c]]
        self.assertEqual(sorted(given), sorted(g.CLUE_CELLS))
        self.assertEqual(board[0][0], "W")


class SolverTests(unittest.TestCase):

    def test_published_puzzles_have_exactly_one_solution(self):
        for words, grid in PUBLISHED:
            positions = g.letter_positions(grid)
            for word in words:
                self.assertTrue(g.is_traceable(word, positions), word)
            self.assertEqual(g.count_solutions(g.clue_letters(grid), words), 1)

    def test_too_few_words_leaves_the_puzzle_ambiguous(self):
        words, grid = PUBLISHED[0]
        self.assertEqual(g.count_solutions(g.clue_letters(grid), words[:1], limit=2), 2)

    def test_contradictory_words_have_no_solution(self):
        # W and B sit in opposite corners, so they can never be adjacent
        words, grid = PUBLISHED[0]
        self.assertEqual(g.count_solutions(g.clue_letters(grid), words + ["WB"]), 0)

    def test_propagation_reaches_a_fixed_point(self):
        """Regression: propagation used to spin forever when a domain was
        narrowed, because the removal was discarded instead of being stored.

        The grid is spelt out rather than generated, so this keeps testing the
        case that actually triggered the bug however grids are built later.
        """
        grid = [["E", "L", "G", "F", "X"],
                ["V", "C", "I", "B", "A"],
                ["T", "S", "J", "O", "M"],
                ["P", "N", "R", "H", "Y"],
                ["U", "W", "Q", "K", "D"]]
        words, _ = g.load_words()
        candidates = g.traceable_words(grid, words)

        self.assertEqual(g.count_solutions(g.clue_letters(grid), candidates), 1)


class ClueLetterTests(unittest.TestCase):
    """A given vowel makes a puzzle much easier, so none are ever given away."""

    def test_grids_never_give_away_a_vowel(self):
        rng = random.Random(11)
        for _ in range(200):
            grid = g.random_grid(rng)
            for row, col in g.CLUE_CELLS:
                self.assertNotIn(grid[row][col], g.VOWELS)

    def test_vowels_are_still_somewhere_on_the_grid(self):
        grid = g.random_grid(random.Random(12))
        letters = "".join("".join(row) for row in grid)
        self.assertEqual(sorted(letters), sorted(g.ALPHABET))

    def test_the_excluded_letters_can_be_changed(self):
        rng = random.Random(13)
        for _ in range(50):
            grid = g.random_grid(rng, keep_off_clues="AEIOUY")
            for row, col in g.CLUE_CELLS:
                self.assertNotIn(grid[row][col], "AEIOUY")

    def test_too_few_clue_letters_is_rejected(self):
        with self.assertRaises(ValueError):
            # Leaves only eight letters for the nine clue cells
            g.random_grid(random.Random(14), keep_off_clues="ABCDEFGHIJKLMNOPQ")


class GenerationTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.words, cls.rank = g.load_words()
        cls.puzzles = g.generate_many(5, "uber", 1, cls.words, cls.rank, seed=1234)

    def test_grid_holds_each_letter_once(self):
        for grid, _, _ in self.puzzles:
            letters = "".join("".join(row) for row in grid)
            self.assertEqual(sorted(letters), sorted(g.ALPHABET))

    def test_words_are_real_and_traceable(self):
        for grid, words, _ in self.puzzles:
            positions = g.letter_positions(grid)
            for word in words:
                self.assertIn(word, self.rank)
                self.assertTrue(g.is_traceable(word, positions), word)

    def test_puzzles_are_uniquely_solvable(self):
        for _, words, clues in self.puzzles:
            self.assertEqual(g.count_solutions(clues, words), 1)

    def test_respects_the_requested_shape(self):
        for _, words, _ in self.puzzles:
            self.assertTrue(9 <= len(words) <= 11)
            self.assertGreaterEqual(len(set("".join(words))), 20)

    def test_no_puzzle_gives_away_a_vowel(self):
        for _, _, clues in self.puzzles:
            self.assertEqual([letter for letter in clues if letter in g.VOWELS], [])

    def test_seed_makes_generation_repeatable(self):
        again = g.generate_many(5, "uber", 1, self.words, self.rank, seed=1234)
        self.assertEqual([p[1] for p in again], [p[1] for p in self.puzzles])

    def test_generate_many_returns_distinct_puzzles(self):
        grids = {"".join("".join(r) for r in p[0]) for p in self.puzzles}
        self.assertEqual(len(grids), len(self.puzzles))


class LayoutTests(unittest.TestCase):
    """Clue layouts, taken from the 2,752 published puzzles of each type."""

    def test_uber_always_uses_the_same_nine_clues(self):
        rng = random.Random(1)
        self.assertEqual(g.clue_cells("uber", 1, rng), list(g.CLUE_CELLS))
        self.assertEqual(g.clue_cells("uber", 7, rng), list(g.CLUE_CELLS))

    def test_ultra_gives_away_less_as_the_week_goes_on(self):
        rng = random.Random(2)
        easiest = len(g.clue_cells("ultra", 1, rng))
        hardest = max(len(layout) for layout in g.ULTRA_LAYOUTS[7])
        self.assertEqual(easiest, 8)
        self.assertLessEqual(hardest, 3)

    def test_hyper_scatters_its_clues(self):
        """Hyper puts clues anywhere, so repeated draws should differ."""
        rng = random.Random(3)
        draws = {tuple(g.clue_cells("hyper", 1, rng)) for _ in range(20)}
        self.assertGreater(len(draws), 1)
        for draw in draws:
            self.assertEqual(len(draw), g.HYPER_CLUE_COUNT[1])

    def test_unknown_type_and_level_are_rejected(self):
        rng = random.Random(4)
        with self.assertRaises(ValueError):
            g.clue_cells("mega", 1, rng)
        with self.assertRaises(ValueError):
            g.generate("uber", level=8)


class ChainTests(unittest.TestCase):
    """Hyper clues are walks over the grid, not words."""

    GRID = [["A", "B", "C", "D", "E"],
            ["F", "G", "H", "I", "J"],
            ["K", "L", "M", "N", "O"],
            ["P", "Q", "R", "S", "T"],
            ["U", "V", "W", "X", "Y"]]

    def test_chains_trace_on_the_grid(self):
        rng = random.Random(5)
        positions = g.letter_positions(self.GRID)
        for _ in range(200):
            chain = g.random_chain(self.GRID, rng, rng.choice(g.CHAIN_LENGTHS))
            self.assertGreaterEqual(len(chain), 2)
            self.assertTrue(g.is_traceable(chain, positions), chain)

    def test_chains_do_not_repeat_a_letter(self):
        rng = random.Random(6)
        for _ in range(100):
            chain = g.random_chain(self.GRID, rng, 5)
            self.assertEqual(len(set(chain)), len(chain), chain)


class SearchBudgetTests(unittest.TestCase):

    def test_an_exhausted_budget_is_not_mistaken_for_a_unique_puzzle(self):
        """A search that runs out of budget must be discarded, never trusted."""
        words, grid = PUBLISHED[0]
        clues = g.clue_letters(grid)

        with self.assertRaises(g.SearchTooHard):
            g.count_solutions(clues, words[:1], limit=2, max_nodes=1)

        self.assertFalse(g.has_unique_solution(clues, words, max_nodes=1))


class UltraAndHyperTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.words, cls.rank = g.load_words()
        cls.puzzles = {
            ("ultra", 1): g.generate("ultra", 1, cls.words, cls.rank, random.Random(21)),
            ("ultra", 7): g.generate("ultra", 7, cls.words, cls.rank, random.Random(27)),
            ("hyper", 1): g.generate("hyper", 1, cls.words, cls.rank, random.Random(31)),
            ("hyper", 7): g.generate("hyper", 7, cls.words, cls.rank, random.Random(37)),
        }

    def test_every_puzzle_was_generated(self):
        for key, puzzle in self.puzzles.items():
            self.assertIsNotNone(puzzle, f"{key} failed to generate")

    def test_clues_are_uniquely_solvable(self):
        for key, (_, strings, clues) in self.puzzles.items():
            self.assertEqual(g.count_solutions(clues, strings), 1, key)

    def test_clues_trace_on_the_grid(self):
        for key, (grid, strings, _) in self.puzzles.items():
            positions = g.letter_positions(grid)
            for string in strings:
                self.assertTrue(g.is_traceable(string, positions), f"{key} {string}")

    def test_ultra_uses_real_words_but_hyper_does_not_have_to(self):
        for (puzzle_type, _), (_, strings, _) in self.puzzles.items():
            if puzzle_type == "ultra":
                for word in strings:
                    self.assertIn(word, self.rank, word)

    def test_clue_counts_match_the_level(self):
        for (puzzle_type, level), (_, _, clues) in self.puzzles.items():
            if puzzle_type == "hyper":
                self.assertEqual(len(clues), g.HYPER_CLUE_COUNT[level])
            else:
                sizes = [len(layout) for layout in g.ULTRA_LAYOUTS[level]]
                self.assertIn(len(clues), sizes)

    def test_no_vowels_are_given_away(self):
        for key, (_, _, clues) in self.puzzles.items():
            self.assertEqual([l for l in clues if l in g.VOWELS], [], key)

    def test_ultra_shows_every_letter_in_its_words(self):
        """Ultra gives away little, so its words cover the whole alphabet -
        2,737 of the 2,752 published ones show all 25 letters."""
        for (puzzle_type, _), (_, strings, _) in self.puzzles.items():
            if puzzle_type == "ultra":
                self.assertEqual(len(set("".join(strings))), 25)


if __name__ == "__main__":
    unittest.main()
