# gogenmaker

Generates original Uber-Gogen puzzles, so the site is not limited to the ones
`gogengetter` scrapes from the archive.

## The rules it works to

A 5x5 grid holds each letter A-Y exactly once (Gogen omits Z). Every clue word
must be traceable on the grid: consecutive letters sit on adjacent cells, where
adjacency includes diagonals - a king move in chess. Nine letters are given
away, at the four corners, the four face-centres and the body centre, and the
solver deduces the other sixteen.

These rules were checked against 200 puzzles pulled from the `uber` table. In
all 200, every word traced as a king move, the nine given cells were exactly
those positions, and the clues plus words admitted exactly one grid.

## Vowels are never given away

A given vowel, especially in the centre, makes a puzzle noticeably easier. The
published puzzles avoid it: across all 2,751 in the `uber` table, each of A, E,
I, O and U turns up in a clue cell only 0.2% to 0.9% of the time, against the
4% you would get by chance.

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

python make_puzzles.py 5                   # five puzzles, printed
python make_puzzles.py 20 --json out.json  # twenty puzzles, as JSON
python make_puzzles.py 1 --seed 42         # reproducible

python -m unittest test_generator          # tests
```

The site side is covered by `gogen.tests.test_generated`, run from `gogensite`
the same way as the other Django tests.

Options: `--min-words` / `--max-words` (default 9-11) and `--min-coverage`,
the fewest distinct letters the word list has to show (default 20).

A puzzle takes about 0.4s to generate.

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

A puzzle is identified by its seed: seed 1 is always the same puzzle, and it is
served at `/uber1`.

```bash
python save_puzzles.py 1 20      # generate seeds 1-20 and store them
python save_puzzles.py 1 20 --replace   # regenerate seeds already stored
```

Puzzles go into `uber_generated`, which has the same columns as `uber` so the
site reads it the same way. Re-running skips seeds that already exist, so it is
safe to top up. Credentials come from `gogensite/.env`, the same file the site
uses; `--dsn` overrides it.

There is no source image, so `puzzle_url` holds the puzzle's address on this
site (`/uber1`) instead. That is what the form posts back to say which puzzle
is being answered.

Seed URLs are capped at seven digits, so `/uber1` reaches a generated puzzle
while `/uber20190120` still reaches the archive - the two can never collide.
Progress is logged against puzzle type `uber_generated` with the seed in place
of the date, keeping it separate from archive progress.

## Output

`generate` returns `(grid, words, clues)`: the solution grid, the clue words,
and the nine given letters mapped to their cells. `puzzle_board` turns a grid
into the board the solver sees, blanks and all, in the same shape the `uber`
table stores.
