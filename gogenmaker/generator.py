"""Generate Uber, Ultra and Hyper Gogen puzzles.

All three are a 5x5 grid holding each letter A-Y exactly once (Gogen omits Z).
Every clue must be traceable on the grid: consecutive letters sit on adjacent
cells, where adjacency includes diagonals - a king move in chess. Some letters
are given away, and the solver deduces the rest.

The three differ in what is given and what the clues are:

  Uber   nine clues - the corners, face-centres and body centre - and around
         ten real words. Every one of the 2,752 published puzzles is laid out
         this way.
  Ultra  the same kind of word clues, but fewer letters given away and more
         words to make up for it. The layout is fixed per difficulty level.
  Hyper  no "real" words at all. The clues are arbitrary letter chains tracing walks
         over the grid, so no vocabulary helps, and as few as two letters are
         given away, at any cells at all.

A puzzle is only fair if the clues admit exactly one grid, so every candidate
is checked with an exact solver before it is used.
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

# Ultra and Hyper get harder as the week goes on, so a puzzle has a level from
# 1 (Monday, easiest) to 7 (Sunday, hardest). Uber has no levels: all 2,752
# published ones use the single layout above.
LEVELS = range(1, 8)

# Ultra keeps fixed layouts, losing clues as the week goes on. Where a level
# lists two, the published puzzles alternate between them about evenly.
ULTRA_LAYOUTS = {
    1: [[(0, 0), (0, 2), (0, 4), (2, 0), (2, 4), (4, 0), (4, 2), (4, 4)]],
    2: [[(0, 0), (0, 2), (0, 4), (2, 1), (2, 3), (4, 0), (4, 2), (4, 4)]],
    3: [[(0, 0), (0, 4), (2, 1), (2, 3), (4, 0), (4, 4)]],
    4: [[(0, 0), (0, 4), (2, 2), (4, 0), (4, 4)],
        [(0, 0), (1, 3), (3, 1), (4, 4)]],
    5: [[(0, 0), (0, 4), (4, 0), (4, 4)],
        [(0, 0), (4, 0), (4, 4)]],
    6: [[(0, 4), (1, 0), (3, 3)],
        [(1, 1), (1, 3), (3, 1), (3, 3)]],
    7: [[(0, 1), (4, 4)],
        [(1, 1), (3, 0), (4, 4)]],
}

# Hyper scatters its clues over any cells at all - the 2,752 published puzzles
# use 1,888 different arrangements - so only the count is fixed per level.
HYPER_CLUE_COUNT = {1: 5, 2: 5, 3: 4, 4: 4, 5: 3, 6: 3, 7: 2}

# How many clue strings to aim for, taken from the published puzzles: the
# fewer letters given away, the more clues are needed to pin the grid down.
WORD_COUNTS = {
    "uber": {level: (9, 11) for level in LEVELS},
    "ultra": {1: (11, 13), 2: (11, 14), 3: (12, 14), 4: (12, 15),
              5: (13, 15), 6: (13, 16), 7: (13, 16)},
    "hyper": {1: (9, 11), 2: (9, 11), 3: (9, 11), 4: (9, 12),
              5: (9, 12), 6: (9, 12), 7: (10, 12)},
}

# Fewest distinct letters the clue strings must between them show
MIN_COVERAGE = {"uber": 20, "ultra": 25, "hyper": 23}

# Hyper chain lengths, matching the spread across the published puzzles
CHAIN_LENGTHS = [2] * 6 + [3] * 34 + [4] * 35 + [5] * 17 + [6] * 6 + [7] * 2

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


def random_grid(rng, cells=CLUE_CELLS, keep_off_clues=VOWELS):
    """A 5x5 grid holding a random permutation of the alphabet.

    Letters in `keep_off_clues` are kept away from `cells`, the ones given
    away. A given vowel makes a puzzle markedly easier, so they are placed
    among the hidden cells by construction rather than by rejecting grids -
    with nine clues, rejection would throw away eleven grids in twelve.
    """
    clue_candidates = [letter for letter in ALPHABET if letter not in keep_off_clues]
    if len(clue_candidates) < len(cells):
        raise ValueError("Too few letters left to fill the clue cells")

    rng.shuffle(clue_candidates)
    given, spare = clue_candidates[:len(cells)], clue_candidates[len(cells):]

    hidden = spare + [letter for letter in ALPHABET if letter in keep_off_clues]
    rng.shuffle(hidden)

    grid = [["" for _ in range(5)] for _ in range(5)]
    for (row, col), letter in zip(cells, given):
        grid[row][col] = letter
    for (row, col), letter in zip([c for c in CELLS if c not in set(cells)], hidden):
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


def clue_letters(grid, cells=CLUE_CELLS):
    """The given letters, mapped to the cell each one occupies."""
    return {grid[r][c]: (r, c) for r, c in cells}


def puzzle_board(grid, cells=CLUE_CELLS):
    """The grid as the solver sees it: clues only, other cells blank."""
    board = [["" for _ in range(5)] for _ in range(5)]
    for r, c in cells:
        board[r][c] = grid[r][c]

    return board


def clue_cells(puzzle_type, level, rng):
    """The cells given away for a puzzle of this type and difficulty."""
    if puzzle_type == "uber":
        return list(CLUE_CELLS)
    if puzzle_type == "ultra":
        return list(rng.choice(ULTRA_LAYOUTS[level]))
    if puzzle_type == "hyper":
        return sorted(rng.sample(CELLS, HYPER_CLUE_COUNT[level]))

    raise ValueError(f"Unknown puzzle type: {puzzle_type}")


class SearchTooHard(Exception):
    """Raised when a puzzle needs more search than the budget allows.

    Hyper puzzles can give away as few as two letters, which leaves a search
    that occasionally runs long. Generation treats this as a reason to discard
    the candidate rather than to trust it, so an unverified puzzle can never
    reach a solver.
    """


def count_solutions(clues, words, limit=2, max_nodes=200000):
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
    nodes = 0

    def search(domains):
        nonlocal solutions, nodes

        nodes += 1
        if max_nodes is not None and nodes > max_nodes:
            raise SearchTooHard()

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


def has_unique_solution(clues, words, max_nodes=200000):
    """True only if exactly one grid fits. A search that blows the budget
    counts as a failure, so an unverified candidate is always discarded."""
    try:
        return count_solutions(clues, words, limit=2, max_nodes=max_nodes) == 1
    except SearchTooHard:
        return False


def choose_words(candidates, clues, rank, rng, min_words, max_words, min_coverage):
    """Pare the candidates down to a small, appealing, still-unique word list.

    Words are dropped least-appealing first, and a drop is kept only when the
    puzzle still has exactly one solution and still shows off enough letters.

    Dropping stops at a target picked from the acceptable range rather than
    grinding down to the minimum, which spreads the word counts out the way
    the published puzzles are spread instead of pinning them to the floor.
    """
    def appeal(word):
        return (
            -rank.get(word, UNRANKED) / 1000.0
            + LENGTH_BONUS.get(len(word), 0)
        )

    target = rng.randint(min_words, max_words)

    kept = list(candidates)
    for word in sorted(candidates, key=lambda w: (appeal(w), rng.random())):
        if len(kept) <= target:
            break

        trial = [w for w in kept if w != word]
        if len(set("".join(trial))) < min_coverage:
            continue
        if has_unique_solution(clues, trial):
            kept = trial

    return sorted(kept)


def random_chain(grid, rng, length):
    """A random walk across the grid, read off as the letters it visits.

    Hyper clues are not words, so there is no dictionary to search: the walk
    is built directly on the grid. It is kept self-avoiding, which matches 96%
    of the published chains - the rest do double back over a letter.
    """
    walk = [rng.choice(CELLS)]

    while len(walk) < length:
        options = sorted(cell for cell in ADJACENT[walk[-1]] if cell not in walk)
        if not options:
            break
        walk.append(rng.choice(options))

    return "".join(grid[row][col] for row, col in walk)


def choose_chains(candidates, clues, rng, min_chains, max_chains, min_coverage):
    """Pare a pool of chains down, keeping the puzzle uniquely solvable."""
    # Middling lengths are what the published puzzles mostly use
    bonus = {2: -6, 3: 8, 4: 8, 5: 4, 6: -2, 7: -6}

    target = rng.randint(min_chains, max_chains)

    kept = list(candidates)
    for chain in sorted(candidates, key=lambda c: (bonus.get(len(c), -10), rng.random())):
        if len(kept) <= target:
            break

        trial = [c for c in kept if c != chain]
        if len(set("".join(trial))) < min_coverage:
            continue
        if has_unique_solution(clues, trial):
            kept = trial

    return sorted(kept)


def generate_word_puzzle(words, rank, rng, cells, min_words, max_words,
                         min_coverage, min_candidates, keep_off_clues):
    """One attempt at an Uber or Ultra puzzle. None if this grid is no good."""
    grid = random_grid(rng, cells, keep_off_clues)
    candidates = traceable_words(grid, words)

    # Too few words to work with, or ambiguous even using every one of them
    if len(candidates) < min_candidates:
        return None

    # Checked before solving: if even the whole pool cannot show enough
    # letters, no subset of it will, and solving is far the costlier step.
    if len(set("".join(candidates))) < min_coverage:
        return None

    clues = clue_letters(grid, cells)
    if not has_unique_solution(clues, candidates):
        return None

    chosen = choose_words(candidates, clues, rank, rng, min_words, max_words, min_coverage)
    if min_words <= len(chosen) <= max_words:
        return grid, chosen, clues

    return None


def generate_chain_puzzle(rng, cells, min_chains, max_chains, min_coverage,
                          keep_off_clues, pool_size=90):
    """One attempt at a Hyper puzzle. None if this grid is no good."""
    grid = random_grid(rng, cells, keep_off_clues)

    candidates = {random_chain(grid, rng, rng.choice(CHAIN_LENGTHS))
                  for _ in range(pool_size)}
    candidates = sorted(chain for chain in candidates if len(chain) >= 2)

    if len(set("".join(candidates))) < min_coverage:
        return None

    clues = clue_letters(grid, cells)
    if not has_unique_solution(clues, candidates):
        return None

    chosen = choose_chains(candidates, clues, rng, min_chains, max_chains, min_coverage)
    if min_chains <= len(chosen) <= max_chains:
        return grid, chosen, clues

    return None


def generate(puzzle_type="uber", level=1, words=None, rank=None, rng=None,
             min_words=None, max_words=None, min_coverage=None,
             min_candidates=12, attempts=5000, keep_off_clues=VOWELS):
    """Build one puzzle, or return None if `attempts` grids all fall short.

    `level` runs from 1 (Monday, easiest) to 7 (Sunday, hardest) and decides
    how many letters are given away. Uber ignores it: every published Uber
    uses the same nine clues.

    Returns (grid, clue strings, clues). `grid` is the solution and `clues`
    maps each given letter to its cell.
    """
    if puzzle_type not in WORD_COUNTS:
        raise ValueError(f"Unknown puzzle type: {puzzle_type}")
    if level not in LEVELS:
        raise ValueError(f"Level must be 1 to 7, got {level}")

    rng = rng or random.Random()

    default_min, default_max = WORD_COUNTS[puzzle_type][level]
    min_words = default_min if min_words is None else min_words
    max_words = default_max if max_words is None else max_words
    if min_coverage is None:
        min_coverage = MIN_COVERAGE[puzzle_type]

    if puzzle_type != "hyper" and words is None:
        words, rank = load_words()

    for _ in range(attempts):
        cells = clue_cells(puzzle_type, level, rng)

        if puzzle_type == "hyper":
            result = generate_chain_puzzle(rng, cells, min_words, max_words,
                                           min_coverage, keep_off_clues)
        else:
            result = generate_word_puzzle(words, rank, rng, cells, min_words,
                                          max_words, min_coverage,
                                          min_candidates, keep_off_clues)

        if result is not None:
            return result

    return None


def generate_many(count, puzzle_type="uber", level=1, words=None, rank=None,
                  seed=None, **options):
    """Generate `count` distinct puzzles."""
    if puzzle_type != "hyper" and words is None:
        words, rank = load_words()

    rng = random.Random(seed)
    puzzles = []
    seen = set()

    while len(puzzles) < count:
        result = generate(puzzle_type, level, words, rank, rng, **options)
        if result is None:
            raise RuntimeError("Could not generate a puzzle within the attempt limit")

        grid = result[0]
        fingerprint = "".join("".join(row) for row in grid)
        if fingerprint in seen:
            continue

        seen.add(fingerprint)
        puzzles.append(result)

    return puzzles
