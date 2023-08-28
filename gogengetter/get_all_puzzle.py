from helper import *
from datetime import datetime, timedelta
import psycopg
import sys

types = ["uber", "ultra", "hyper"]

puzzle_type = sys.argv[1]

if puzzle_type not in types:
    raise Exception(f"Invalid puzzle type: Choose uber, ultra or hyper. \"{puzzle_type}\" provided.")

urls = read_tables(puzzle_type)

amount = 0

if len(sys.argv) > 2:
    amount = int(sys.argv[2])

if amount > 0:
    urls = urls[:int(amount-1)]

yesterday_puzzle_date = urls[0][0].split('/')[-1][-15:-7]
today_puzzle_date = (datetime.strptime(yesterday_puzzle_date, "%Y%m%d") + timedelta(days=1)).strftime('%Y%m%d')

url_stub = f"http://www.puzzles.grosse.is-a-geek.com/images/gog/puz/{puzzle_type}/{puzzle_type}{today_puzzle_date}"
urls.insert(0, (f"{url_stub}puz.png", f"{url_stub}sol.png"))

with psycopg.connect("dbname=gogen user=postgresmd5") as conn:
    with conn.cursor() as cur:
        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS {puzzle_type}(
            puzzle_name text NOT NULL PRIMARY KEY,
            puzzle_url text,
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

    puzzle_name = puz_url.split('/')[-1][:-7]

    print((puzzle_name, puz_url, sol_url, words, puzzle_board, solution_board))

    with psycopg.connect("dbname=gogen user=postgresmd5") as conn:
        with conn.cursor() as cur:
            cur.execute(f"""
                INSERT INTO {puzzle_type}(puzzle_name, puzzle_url, solution_url, words, puzzle_board, solution_board)
                VALUES(%s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING;
            """, (puzzle_name, puz_url, sol_url, words, puzzle_board, solution_board))

            conn.commit()
