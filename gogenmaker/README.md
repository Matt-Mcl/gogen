# gogenmaker

Generates original Uber, Ultra and Hyper Gogen puzzles, so the site is not
limited to the ones `gogengetter` scrapes from the archive.

## The rules it works to

A 5x5 grid holds each letter A-Y exactly once (Gogen omits Z). Every clue must
be traceable on the grid: consecutive letters sit on adjacent cells, where
adjacency includes diagonals - a king move in chess. Some letters are given
away and the solver deduces the rest.

The three types differ in what is given and what the clues are. All of this
was measured from the 2,752 puzzles of each type already in the database
rather than assumed:

| | clues given | clue strings | what the clues are |
|---|---|---|---|
| Uber | 9, always the same cells | ~10 | real words |
| Ultra | 8 down to 2 by level | ~12-15 | real words |
| Hyper | 5 down to 2 by level, any cells | ~10 | letter chains, not words |

**Uber** never varies: all 2,752 published ones give away the corners, the
face-centres and the body centre.

**Ultra** is the same puzzle with less help. It keeps fixed layouts that shed
clues as the week goes on, and adds words to make up for it. Its words cover
the whole alphabet - 2,737 of the 2,752 published ones show all 25 letters.

**Hyper** is a different puzzle. Its clues are not words at all but arbitrary
letter chains tracing walks over the grid, so no vocabulary helps: 22,796 of
the 23,574 published Hyper clue strings are not in the Scrabble dictionary,
and 4% double back over a letter, which no real Gogen word does. Its clues sit
at any cells at all - the published puzzles use 1,888 different arrangements.

Difficulty runs from level 1 (Monday, easiest) to 7 (Sunday, hardest), which
is how the source site does it. Uber ignores the level.

The solver was checked against the published puzzles of each type: every Uber
and Ultra sampled had exactly one solution, every word traced as a king move,
and the given cells matched the layouts above.

## Vowels are never given away

A given vowel, especially in the centre, makes a puzzle noticeably easier. The
published Uber puzzles avoid it: across all 2,752, each of A, E, I, O and U
turns up in a clue cell only 0.2% to 0.9% of the time, against the 4% you
would get by chance.

Published Ultra and Hyper puzzles do *not* avoid vowels - they sit near 3-4%,
about what chance gives. The rule is applied to all three types here anyway,
which makes the generated Ultra and Hyper slightly harder than the originals.
Pass `keep_off_clues=""` to `generate` to give vowels away like the source
site does.

Here they are ruled out entirely. Vowels are placed among the hidden cells when
the grid is built, rather than by generating grids and throwing away the ones
that give a vowel away - only about one grid in twelve would survive that.

Y is deliberately not on the list. The published puzzles give it away in 1.48%
of clue cells, several times more often than any true vowel, so it behaves as a
consonant here. To hide it too, pass `keep_off_clues="AEIOUY"` to `generate` or
`random_grid`, or change the `VOWELS` constant.

## Usage

```bash
cd gogenmaker

python make_puzzles.py 5                        # five Uber puzzles, printed
python make_puzzles.py 3 --type ultra --level 5
python make_puzzles.py 3 --type hyper --level 7
python make_puzzles.py 20 --json out.json       # as JSON
python make_puzzles.py 1 --seed 42              # reproducible

python -m unittest test_generator               # tests
```

The site side is covered by `gogen.tests.test_generated`, run from `gogensite`
the same way as the other Django tests.

`--min-words` / `--max-words` / `--min-coverage` override the per-type,
per-level defaults; left alone they follow the published puzzles.

Generation time climbs steeply as clues are taken away, because most of it
goes on grids that get thrown out rather than on the chosen puzzle:

| level | 1 | 3 | 5 | 7 |
|---|---|---|---|---|
| Uber | 0.4s | - | - | - |
| Ultra | 1.5s | 2.9s | 6.6s | 23.5s |
| Hyper | 1.6s | 10.0s | 16.0s | ~20s |

Hardest-level Ultra can take half a minute per puzzle, so generate a batch and
leave it running rather than expecting it to be instant.

## How generation works

1. Shuffle the alphabet into a grid.
2. Scan the dictionary for every word traceable on it, typically around 130.
3. Take the nine clue cells and check the grid is the *only* one those clues and
   words allow. If not, throw the grid away - roughly nine in ten are discarded.
4. Drop words one at a time, least appealing first, keeping each drop only while
   the puzzle still has a single solution and still shows enough letters.

Step 3 is what makes a puzzle fair, so it is also used to verify the finished
article. Solving is treated as a constraint problem - place each letter in a
cell, all distinct, respecting every adjacency the words demand - with domains
narrowed by propagation before anything is guessed.

## The dictionary

`words.txt` holds 48,608 words: the Collins Scrabble list filtered by the Gogen
rules (at least three letters, no Z, no letter used twice). A Scrabble list
suits this well - it carries the obscure words the published puzzles enjoy
(BOYLA, CITHRENS, SAWNEY, WYTE) while excluding abbreviations and proper nouns,
which a plain word list is full of. It covers every word in the 200 sampled
puzzles bar nine, and those nine look like scraper misreads.

The file is ordered most common first, so a word's line number is its frequency
rank. Generation uses that to prefer familiar words, and to prefer the 4-6
letter lengths the published puzzles favour.

## Saving puzzles and playing them

A puzzle is identified by its type and seed: uber seed 1 is always the same
puzzle, and it is served at `/uber1`. Ultra and Hyper work the same way at
`/ultra1` and `/hyper1`.

```bash
python save_puzzles.py 1 20                   # uber seeds 1-20
python save_puzzles.py 1 14 --type ultra      # levels cycle Mon-Sun
python save_puzzles.py 1 20 --type hyper --level 7   # all hardest
python save_puzzles.py 1 20 --replace         # regenerate stored seeds
```

By default a seed's level cycles Monday to Sunday, so seeds 1-7 run easiest to
hardest and seed 8 starts over. `--level` pins every seed to one difficulty.

Puzzles go into `uber_generated`, `ultra_generated` and `hyper_generated`,
each with the same columns as the scraped tables so the site reads them the
same way. Re-running skips seeds that already exist, so it is safe to top up.
Credentials come from `gogensite/.env`, the same file the site uses; `--dsn`
overrides it.

There is no source image, so `puzzle_url` holds the puzzle's address on this
site (`/uber1`) instead. That is what the form posts back to say which puzzle
is being answered.

Seed URLs are capped at seven digits, so `/ultra1` reaches a generated puzzle
while `/ultra20190120` still reaches the archive - the two can never collide.
Progress is logged against puzzle type `uber_generated`, `ultra_generated` or
`hyper_generated` with the seed in place of the date, keeping it separate from
archive progress.

## Output

`generate` returns `(grid, words, clues)`: the solution grid, the clue words,
and the nine given letters mapped to their cells. `puzzle_board` turns a grid
into the board the solver sees, blanks and all, in the same shape the `uber`
table stores.
