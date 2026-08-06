"""Generate Uber-Gogen puzzles.

An Uber-Gogen is a 5x5 grid holding each letter A-Y exactly once (no Z).
Every clue word must be traceable on the grid: consecutive letters of the
word sit on adjacent cells, where adjacency includes diagonals (a king move
in chess). Nine letters are given away as clues - the four corners, the four
face-centres and the body centre - and the solver deduces the other sixteen.

A puzzle is only fair if those clues plus the word list admit exactly one
grid, so every candidate is checked with an exact solver before it is used.
"""

import os
import random
from itertools import product

ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXY"  # the Gogen alphabet omits Z
CELLS = [(r, c) for r in range(5) for c in range(5)]

# Corners, face-centres and the body centre, matching the published puzzles
CLUE_CELLS = [(0, 0), (0, 2), (0, 4),
              (2, 0), (2, 2), (2, 4),
              (4, 0), (4, 2), (4, 4)]

# Cells reachable by a king move, precomputed once
ADJACENT = {
    (r, c): frozenset(
        (r + dr, c + dc)
        for dr, dc in product((-1, 0, 1), repeat=2)
        if (dr or dc) and 0 <= r + dr < 5 and 0 <= c + dc < 5
    )
    for r, c in CELLS
}

# Never given away as a clue. Y is left out: the published puzzles treat it as
# a consonant for this purpose, giving it away far more often than A, E, I, O
# or U. Add it here to keep it hidden too.
VOWELS = "AEIOU"

WORDS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "words.txt")

# The published puzzles lean on 4-6 letter words and use 3-letter words sparingly
LENGTH_BONUS = {3: -25, 4: 6, 5: 14, 6: 16, 7: 12, 8: 8, 9: 4}

# Score for a word absent from the frequency data, so unranked words sort last
UNRANKED = 10 ** 6


def load_words(path=WORDS_FILE):
    """Read the dictionary. It is stored most-common-first, so a word's line
    number is its frequency rank. Returns (words, rank-by-word)."""
    with open(path) as f:
        words = [line.strip() for line in f if line.strip()]

    return words, {word: rank for rank, word in enumerate(words)}


def random_grid(rng, keep_off_clues=VOWELS):
    """A 5x5 grid holding a random permutation of the alphabet.

    Letters in `keep_off_clues` are kept away from the nine given cells. A
    given vowel makes a puzzle markedly easier, and the published ones almost
    never do it, so they are placed among the hidden cells by construction
    rather than by rejecting grids - rejection would throw away roughly
    eleven grids in twelve.
    """
    clue_candidates = [letter for letter in ALPHABET if letter not in keep_off_clues]
    if len(clue_candidates) < len(CLUE_CELLS):
        raise ValueError("Too few letters left to fill the clue cells")

    rng.shuffle(clue_candidates)
    given, spare = clue_candidates[:len(CLUE_CELLS)], clue_candidates[len(CLUE_CELLS):]

    hidden = spare + [letter for letter in ALPHABET if letter in keep_off_clues]
    rng.shuffle(hidden)

    grid = [["" for _ in range(5)] for _ in range(5)]
    for (row, col), letter in zip(CLUE_CELLS, given):
        grid[row][col] = letter
    for (row, col), letter in zip([c for c in CELLS if c not in set(CLUE_CELLS)], hidden):
        grid[row][col] = letter

    return grid


def letter_positions(grid):
    return {grid[r][c]: (r, c) for r, c in CELLS}


def is_traceable(word, positions):
    """True if every consecutive pair of letters sits on adjacent cells."""
    return all(
        positions[word[i + 1]] in ADJACENT[positions[word[i]]]
        for i in range(len(word) - 1)
    )


def traceable_words(grid, words):
    """Every dictionary word that can be traced on the grid."""
    positions = letter_positions(grid)

    return [word for word in words if is_traceable(word, positions)]


def clue_letters(grid):
    """The nine given letters, mapped to the cell each one occupies."""
    return {grid[r][c]: (r, c) for r, c in CLUE_CELLS}


def puzzle_board(grid):
    """The grid as the solver sees it: clues only, other cells blank."""
    board = [["" for _ in range(5)] for _ in range(5)]
    for r, c in CLUE_CELLS:
        board[r][c] = grid[r][c]

    return board


def count_solutions(clues, words, limit=2):
    """Count the grids satisfying the clues and words, stopping at `limit`.

    Solving is a constraint problem: place each letter in a cell, all cells
    distinct, with every adjacency demanded by the words respected. Domains
    are narrowed by propagation and only then guessed at, which keeps the
    search small enough to run thousands of times during generation.
    """
    # Each consecutive pair in a word forces those two letters to be adjacent
    neighbours = {letter: set() for letter in ALPHABET}
    for word in words:
        for a, b in zip(word, word[1:]):
            neighbours[a].add(b)
            neighbours[b].add(a)

    free_cells = set(CELLS) - set(clues.values())
    domains = {
        letter: {clues[letter]} if letter in clues else set(free_cells)
        for letter in ALPHABET
    }

    def propagate(domains):
        """Narrow domains to a fixed point. False if a letter runs out of cells."""
        changed = True
        while changed:
            changed = False

            # A letter with one cell left claims it, so no other letter may use it
            claimed = {}
            for letter, cells in domains.items():
                if len(cells) == 1:
                    cell = next(iter(cells))
                    if cell in claimed:
                        return False
                    claimed[cell] = letter

            for letter, cells in domains.items():
                if len(cells) > 1:
                    kept = cells - claimed.keys()
                    if len(kept) < len(cells):
                        domains[letter] = kept
                        if not kept:
                            return False
                        changed = True

            # A cell is only viable if each required neighbour can sit beside it
            for letter in ALPHABET:
                for other in neighbours[letter]:
                    viable = {
                        cell for cell in domains[letter]
                        if ADJACENT[cell] & domains[other]
                    }
                    if len(viable) < len(domains[letter]):
                        domains[letter] = viable
                        if not viable:
                            return False
                        changed = True

        return True

    solutions = 0

    def search(domains):
        nonlocal solutions
        if not propagate(domains):
            return

        undecided = [letter for letter in ALPHABET if len(domains[letter]) > 1]
        if not undecided:
            solutions += 1
            return

        # Guess the most constrained letter first to fail fast
        letter = min(undecided, key=lambda x: (len(domains[x]), -len(neighbours[x])))
        for cell in sorted(domains[letter]):
            branch = {key: set(value) for key, value in domains.items()}
            branch[letter] = {cell}
            search(branch)
            if solutions >= limit:
                return

    search(domains)

    return solutions


def has_unique_solution(clues, words):
    return count_solutions(clues, words, limit=2) == 1


def choose_words(candidates, clues, rank, rng, min_words, min_coverage):
    """Pare the candidates down to a small, appealing, still-unique word list.

    Words are dropped least-appealing first, and a drop is kept only when the
    puzzle still has exactly one solution and still shows off enough letters.
    """
    def appeal(word):
        return (
            -rank.get(word, UNRANKED) / 1000.0
            + LENGTH_BONUS.get(len(word), 0)
        )

    kept = list(candidates)
    for word in sorted(candidates, key=lambda w: (appeal(w), rng.random())):
        if len(kept) <= min_words:
            break

        trial = [w for w in kept if w != word]
        if len(set("".join(trial))) < min_coverage:
            continue
        if has_unique_solution(clues, trial):
            kept = trial

    return sorted(kept)


def generate(words, rank, rng=None, min_words=9, max_words=11,
             min_coverage=20, min_candidates=12, attempts=2000,
             keep_off_clues=VOWELS):
    """Build one puzzle, or return None if `attempts` grids all fall short.

    Returns (grid, words, clues). `grid` is the solution; `words` is the clue
    list; `clues` maps each given letter to its cell.
    """
    rng = rng or random.Random()

    for _ in range(attempts):
        grid = random_grid(rng, keep_off_clues)
        candidates = traceable_words(grid, words)

        # Too few words to work with, or ambiguous even using every one of them
        if len(candidates) < min_candidates:
            continue

        clues = clue_letters(grid)
        if not has_unique_solution(clues, candidates):
            continue

        chosen = choose_words(candidates, clues, rank, rng, min_words, min_coverage)
        if min_words <= len(chosen) <= max_words:
            return grid, chosen, clues

    return None


def generate_many(count, words=None, rank=None, seed=None, **options):
    """Generate `count` distinct puzzles."""
    if words is None:
        words, rank = load_words()

    rng = random.Random(seed)
    puzzles = []
    seen = set()

    while len(puzzles) < count:
        result = generate(words, rank, rng, **options)
        if result is None:
            raise RuntimeError("Could not generate a puzzle within the attempt limit")

        grid = result[0]
        fingerprint = "".join("".join(row) for row in grid)
        if fingerprint in seen:
            continue

        seen.add(fingerprint)
        puzzles.append(result)

    return puzzles
