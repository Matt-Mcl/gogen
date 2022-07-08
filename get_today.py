from helper import *
import psycopg

get_tables()
urls = read_tables()

puzzle_board = get_board(urls[0][0])
solution_board = get_board(urls[0][1])
words = get_words(urls[0][0])

print((urls[0], words, puzzle_board, solution_board))

with psycopg.connect("dbname=gogen user=postgres") as conn:
    with conn.cursor() as cur:
        cur.execute(f"""
            INSERT INTO puzzles(puzzle_url, solution_url, words, puzzle_board, solution_board)
            VALUES(%s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING;
        """, (urls[0][0], urls[0][1], words, puzzle_board, solution_board))
