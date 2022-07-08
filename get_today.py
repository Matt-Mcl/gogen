from helper import *
import psycopg

get_tables()
urls = read_tables("uber")
today = urls[0]

puzzle_board = get_board(today[0])
solution_board = get_board(today[1])
words = get_words(today[0])

print((today, words, puzzle_board, solution_board))

with psycopg.connect("dbname=gogen user=postgresmd5") as conn:
    with conn.cursor() as cur:
        cur.execute(f"""
            INSERT INTO puzzles(puzzle_url, solution_url, words, puzzle_board, solution_board)
            VALUES(%s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING;
        """, (today[0], today[1], words, puzzle_board, solution_board))
