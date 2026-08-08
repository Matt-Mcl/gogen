"""Generate puzzles and save them to the <type>_generated tables.

A puzzle is identified by its type and seed, so uber seed 1 is always the same
puzzle and is served at /uber1. Re-running this is safe: existing seeds are
left alone unless --replace is given.

Ultra and Hyper get harder as the week goes on, so by default a seed's level
cycles Monday to Sunday: seeds 1 to 7 run easiest to hardest, seed 8 starts
over. Use --level to pin every seed to one difficulty instead. Uber has no
levels - every published one gives away the same nine letters.

Generating a puzzle takes seconds, so seeds are spread over worker processes.
A seed decides its puzzle by itself, so this changes nothing about the result.

Examples:
    python save_puzzles.py 1 20                    # uber seeds 1 to 20
    python save_puzzles.py 1 20 --type ultra       # ultra, levels cycling
    python save_puzzles.py 1 20 --type hyper --level 7
    python save_puzzles.py 1 10 --replace
    python save_puzzles.py 1 100 --jobs 6          # more workers
"""

import argparse
import os
import random
import sys
from concurrent.futures import ProcessPoolExecutor

import psycopg
from dotenv import load_dotenv

from generator import LEVELS, generate, load_words, puzzle_board

PUZZLE_TYPES = ("uber", "ultra", "hyper")

# Generation is CPU-bound Python, so it needs processes rather than threads:
# threads would take turns holding the GIL and run no faster than one.
DEFAULT_JOBS = 5

# The dictionary, loaded once per worker process by init_worker
_words = None
_rank = None


def table_name(puzzle_type):
    return f"{puzzle_type}_generated"


def level_for(seed, level=None):
    """Difficulty for a seed: fixed if given, otherwise cycling Monday to Sunday."""
    return level if level is not None else (seed - 1) % 7 + 1


def connection_string():
    """Build the DSN from the same .env the Django site reads."""
    env = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "gogensite", ".env")
    load_dotenv(env)

    return (
        f"dbname={os.getenv('PG_PUZZLE_DBNAME')} "
        f"user={os.getenv('PG_PUZZLE_USER')} "
        f"password={os.getenv('PG_PUZZLE_PASSWORD')} "
        f"host={os.getenv('PG_HOST')} "
        f"port={os.getenv('PG_PORT')}"
    )


def create_table(conn, puzzle_type):
    """Same shape as the scraped tables, so the site can read it the same way."""
    conn.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name(puzzle_type)}(
        puzzle_name text NOT NULL PRIMARY KEY,
        puzzle_url text,
        solution_url text,
        words text[],
        puzzle_board text[],
        solution_board text[]
        );
    """)


def existing_seeds(conn, puzzle_type, seeds):
    """Which of `seeds` are already stored."""
    names = [f"{puzzle_type}{seed}" for seed in seeds]
    rows = conn.execute(
        f"SELECT puzzle_name FROM {table_name(puzzle_type)} WHERE puzzle_name = ANY(%s);",
        (names,),
    ).fetchall()

    return {int(row[0][len(puzzle_type):]) for row in rows}


def build(puzzle_type, seed, level, words, rank, **options):
    """Generate the puzzle for `seed`. The type, seed and level decide it fully."""
    result = generate(puzzle_type, level, words, rank, random.Random(seed), **options)
    if result is None:
        raise RuntimeError(f"Could not generate a {puzzle_type} puzzle for seed {seed}")

    grid, chosen, clues = result

    return {
        "puzzle_name": f"{puzzle_type}{seed}",
        # There is no source image, so the URL doubles as the puzzle's address
        # on this site. The form posts it back to identify the puzzle.
        "puzzle_url": f"/{puzzle_type}{seed}",
        "solution_url": "",
        "words": chosen,
        # Hyper scatters its clues, so the given cells vary from puzzle to puzzle
        "puzzle_board": puzzle_board(grid, clues.values()),
        "solution_board": grid,
    }


def init_worker():
    """Load the dictionary once per worker, rather than sending it per seed."""
    global _words, _rank
    _words, _rank = load_words()


def build_job(job):
    """Worker entry point: one seed, built from the dictionary this process holds."""
    puzzle_type, seed, level, options = job

    return build(puzzle_type, seed, level, _words, _rank, **options)


def build_all(jobs, workers):
    """Yield each job's puzzle, in the order given, generating `workers` at once.

    Seeds are independent - `build` gives each its own random.Random(seed) - so
    sharing them out leaves every puzzle exactly as it would have been built one
    at a time. Only the order they finish in changes, and that is put back here.
    """
    if workers == 1 or len(jobs) < 2:
        words, rank = load_words()
        for puzzle_type, seed, level, options in jobs:
            yield build(puzzle_type, seed, level, words, rank, **options)

        return

    with ProcessPoolExecutor(min(workers, len(jobs)),
                             initializer=init_worker) as pool:
        # One seed per task: they take seconds each, so there is nothing to gain
        # from batching them, and handing them out singly keeps the workers even
        yield from pool.map(build_job, jobs)


def save(conn, puzzle, puzzle_type, replace=False):
    conflict = (
        """DO UPDATE SET puzzle_url = EXCLUDED.puzzle_url,
                         solution_url = EXCLUDED.solution_url,
                         words = EXCLUDED.words,
                         puzzle_board = EXCLUDED.puzzle_board,
                         solution_board = EXCLUDED.solution_board"""
        if replace else "DO NOTHING"
    )

    conn.execute(
        f"""
        INSERT INTO {table_name(puzzle_type)}(puzzle_name, puzzle_url, solution_url,
                            words, puzzle_board, solution_board)
        VALUES(%s, %s, %s, %s, %s, %s)
        ON CONFLICT (puzzle_name) {conflict};
        """,
        (puzzle["puzzle_name"], puzzle["puzzle_url"], puzzle["solution_url"],
         puzzle["words"], puzzle["puzzle_board"], puzzle["solution_board"]),
    )


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Generate Gogen puzzles and save them to the database.")
    parser.add_argument("first", type=int, help="first seed")
    parser.add_argument("last", type=int, nargs="?",
                        help="last seed, inclusive (defaults to first)")
    parser.add_argument("--type", choices=PUZZLE_TYPES, default="uber",
                        help="which puzzle type to generate (default uber)")
    parser.add_argument("--level", type=int, choices=list(LEVELS),
                        help="pin every seed to one difficulty, 1 easiest to 7 hardest")
    parser.add_argument("--replace", action="store_true",
                        help="regenerate seeds that are already stored")
    parser.add_argument("--dsn", help="override the database connection string")
    parser.add_argument("--min-words", type=int,
                        help="fewest clue strings (defaults to suit the type and level)")
    parser.add_argument("--max-words", type=int,
                        help="most clue strings (defaults to suit the type and level)")
    parser.add_argument("--min-coverage", type=int,
                        help="fewest distinct letters the clues must show")
    parser.add_argument("--jobs", type=int, default=DEFAULT_JOBS,
                        help=f"how many seeds to generate at once "
                             f"(default {DEFAULT_JOBS}, 1 to stay in this process)")
    args = parser.parse_args(argv)

    last = args.last if args.last is not None else args.first
    if args.first < 1:
        parser.error("seeds start at 1")
    if last < args.first:
        parser.error("last seed cannot be before the first")
    if args.min_words and args.max_words and args.min_words > args.max_words:
        parser.error("--min-words cannot exceed --max-words")
    if args.jobs < 1:
        parser.error("--jobs must be at least 1")

    puzzle_type = args.type
    seeds = range(args.first, last + 1)
    # Leave each unset option to the per-type, per-level default
    options = {name: value for name, value in (
        ("min_words", args.min_words),
        ("max_words", args.max_words),
        ("min_coverage", args.min_coverage),
    ) if value is not None}

    with psycopg.connect(args.dsn or connection_string()) as conn:
        create_table(conn, puzzle_type)
        conn.commit()

        skip = set() if args.replace else existing_seeds(conn, puzzle_type, seeds)
        if skip:
            print(f"Skipping {len(skip)} seed(s) already stored")

        jobs = [(puzzle_type, seed, level_for(seed, args.level), options)
                for seed in seeds if seed not in skip]

        # The workers only generate: the connection stays here, in one process
        saved = 0
        for (_, _, level, _), puzzle in zip(jobs, build_all(jobs, args.jobs)):
            save(conn, puzzle, puzzle_type, replace=args.replace)
            conn.commit()
            saved += 1
            print(f"{puzzle['puzzle_name']} (level {level}): {', '.join(puzzle['words'])}")

        print(f"\nSaved {saved} puzzle(s) to {table_name(puzzle_type)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
