from helper import *
from time import sleep
import psycopg

get_tables()
urls = read_tables()

for puz_url, sol_url in urls:
    puzzle_board = get_board(puz_url)
    solution_board = get_board(sol_url)
    words = get_words(puz_url)

    print((puz_url, sol_url, words, puzzle_board, solution_board))

    with psycopg.connect("dbname=gogen user=postgres") as conn:
        with conn.cursor() as cur:
            cur.execute(f"""
                INSERT INTO puzzles(puzzle_url, solution_url, words, puzzle_board, solution_board)
                VALUES(%s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING;
            """, (puz_url, sol_url, words, puzzle_board, solution_board))

    sleep(1)
