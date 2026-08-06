"""Generate puzzles and save them to the uber_generated table.

A puzzle is identified by its seed, so seed 1 is always the same puzzle and is
served at /uber1. Re-running this is safe: existing seeds are left alone unless
--replace is given.

Examples:
    python save_puzzles.py 1 20          # seeds 1 to 20
    python save_puzzles.py 5             # seed 5 only
    python save_puzzles.py 1 10 --replace
"""

import argparse
import os
import random
import sys

import psycopg
from dotenv import load_dotenv

from generator import generate, load_words, puzzle_board

TABLE = "uber_generated"


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


def create_table(conn):
    """Same shape as the uber table, so the site can read it the same way."""
    conn.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLE}(
        puzzle_name text NOT NULL PRIMARY KEY,
        puzzle_url text,
        solution_url text,
        words text[],
        puzzle_board text[],
        solution_board text[]
        );
    """)


def existing_seeds(conn, seeds):
    """Which of `seeds` are already stored."""
    names = [f"uber{seed}" for seed in seeds]
    rows = conn.execute(
        f"SELECT puzzle_name FROM {TABLE} WHERE puzzle_name = ANY(%s);", (names,)
    ).fetchall()

    return {int(row[0][4:]) for row in rows}


def build(seed, words, rank, **options):
    """Generate the puzzle for `seed`. The seed alone decides the puzzle."""
    result = generate(words, rank, random.Random(seed), **options)
    if result is None:
        raise RuntimeError(f"Could not generate a puzzle for seed {seed}")

    grid, chosen, _ = result

    return {
        "puzzle_name": f"uber{seed}",
        # There is no source image, so the URL doubles as the puzzle's address
        # on this site. The form posts it back to identify the puzzle.
        "puzzle_url": f"/uber{seed}",
        "solution_url": "",
        "words": chosen,
        "puzzle_board": puzzle_board(grid),
        "solution_board": grid,
    }


def save(conn, puzzle, replace=False):
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
        INSERT INTO {TABLE}(puzzle_name, puzzle_url, solution_url,
                            words, puzzle_board, solution_board)
        VALUES(%s, %s, %s, %s, %s, %s)
        ON CONFLICT (puzzle_name) {conflict};
        """,
        (puzzle["puzzle_name"], puzzle["puzzle_url"], puzzle["solution_url"],
         puzzle["words"], puzzle["puzzle_board"], puzzle["solution_board"]),
    )


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Generate Uber-Gogen puzzles and save them to the database.")
    parser.add_argument("first", type=int, help="first seed")
    parser.add_argument("last", type=int, nargs="?",
                        help="last seed, inclusive (defaults to first)")
    parser.add_argument("--replace", action="store_true",
                        help="regenerate seeds that are already stored")
    parser.add_argument("--dsn", help="override the database connection string")
    parser.add_argument("--min-words", type=int, default=9)
    parser.add_argument("--max-words", type=int, default=11)
    parser.add_argument("--min-coverage", type=int, default=20)
    args = parser.parse_args(argv)

    last = args.last if args.last is not None else args.first
    if args.first < 1:
        parser.error("seeds start at 1")
    if last < args.first:
        parser.error("last seed cannot be before the first")

    seeds = range(args.first, last + 1)
    options = {
        "min_words": args.min_words,
        "max_words": args.max_words,
        "min_coverage": args.min_coverage,
    }

    words, rank = load_words()

    with psycopg.connect(args.dsn or connection_string()) as conn:
        create_table(conn)
        conn.commit()

        skip = set() if args.replace else existing_seeds(conn, seeds)
        if skip:
            print(f"Skipping {len(skip)} seed(s) already stored")

        saved = 0
        for seed in seeds:
            if seed in skip:
                continue

            puzzle = build(seed, words, rank, **options)
            save(conn, puzzle, replace=args.replace)
            conn.commit()
            saved += 1
            print(f"{puzzle['puzzle_name']}: {', '.join(puzzle['words'])}")

        print(f"\nSaved {saved} puzzle(s) to {TABLE}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
