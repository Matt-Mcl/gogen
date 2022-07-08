from helper import *
import psycopg

get_tables()
urls = read_tables("ultra")

with psycopg.connect("dbname=gogen user=postgresmd5") as conn:
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ultra(
            puzzle_url text NOT NULL PRIMARY KEY,
            solution_url text,
            words text[],
            puzzle_board text[],
            solution_board text[]
            );
        """)

for puz_url, sol_url in urls:
    puzzle_board = get_board(puz_url)
    solution_board = get_board(sol_url)
    words = get_words(puz_url)

    print((puz_url, sol_url, words, puzzle_board, solution_board))

    with psycopg.connect("dbname=gogen user=postgresmd5") as conn:
        with conn.cursor() as cur:
            cur.execute(f"""
                INSERT INTO ultra(puzzle_url, solution_url, words, puzzle_board, solution_board)
                VALUES(%s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING;
            """, (puz_url, sol_url, words, puzzle_board, solution_board))
