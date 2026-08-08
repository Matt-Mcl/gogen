"""Command line front end for the Uber-Gogen generator.

Examples:
    python make_puzzles.py 5                  # five puzzles, printed
    python make_puzzles.py 20 --json out.json # twenty puzzles, as JSON
    python make_puzzles.py 1 --seed 42        # reproducible
"""

import argparse
import json
import sys

from generator import LEVELS, generate_many, load_words, puzzle_board


def format_puzzle(grid, words, clues, index, hide_solution=False):
    lines = [f"--- puzzle {index}", "", "puzzle:"]

    board = puzzle_board(grid, clues.values())
    for row in board:
        lines.append("  " + " ".join(cell or "." for cell in row))

    if not hide_solution:
        lines += ["", "solution:"]
        for row in grid:
            lines.append("  " + " ".join(row))

    lines += ["", "words: " + ", ".join(words), ""]

    return "\n".join(lines)


def as_dict(grid, words, clues):
    return {
        "words": words,
        "puzzle_board": puzzle_board(grid, clues.values()),
        "solution_board": grid,
        "clues": {letter: list(cell) for letter, cell in sorted(clues.items())},
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Generate Uber-Gogen puzzles.")
    parser.add_argument("count", type=int, nargs="?", default=1,
                        help="how many puzzles to generate (default 1)")
    parser.add_argument("--type", choices=("uber", "ultra", "hyper"), default="uber",
                        help="which puzzle type to generate (default uber)")
    parser.add_argument("--level", type=int, choices=list(LEVELS), default=1,
                        help="difficulty, 1 easiest to 7 hardest (ultra and hyper only)")
    parser.add_argument("--seed", type=int, default=None,
                        help="seed the random number generator for repeatable output")
    parser.add_argument("--json", metavar="FILE",
                        help="write the puzzles to FILE as JSON instead of printing them")
    parser.add_argument("--min-words", type=int,
                        help="fewest clue strings (defaults to suit the type and level)")
    parser.add_argument("--max-words", type=int,
                        help="most clue strings (defaults to suit the type and level)")
    parser.add_argument("--min-coverage", type=int,
                        help="fewest distinct letters the clues must show")
    parser.add_argument("--hide-solution", action="store_true",
                        help="hide the solution in the output (default false)")
    args = parser.parse_args(argv)

    if args.count < 1:
        parser.error("count must be at least 1")
    if args.min_words and args.max_words and args.min_words > args.max_words:
        parser.error("--min-words cannot exceed --max-words")

    words, rank = load_words()
    # Leave each unset option to the per-type, per-level default
    options = {name: value for name, value in (
        ("min_words", args.min_words),
        ("max_words", args.max_words),
        ("min_coverage", args.min_coverage),
    ) if value is not None}

    puzzles = generate_many(args.count, args.type, args.level, words, rank,
                            seed=args.seed, **options)

    if args.json:
        payload = [as_dict(*puzzle) for puzzle in puzzles]
        with open(args.json, "w") as f:
            json.dump(payload, f, indent=2)
        print(f"Wrote {len(payload)} puzzles to {args.json}")
    else:
        for index, (grid, chosen, clues) in enumerate(puzzles, start=1):
            print(format_puzzle(grid, chosen, clues, index, hide_solution=args.hide_solution))

    return 0


if __name__ == "__main__":
    sys.exit(main())
