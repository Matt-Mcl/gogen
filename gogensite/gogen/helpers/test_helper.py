import psycopg
from django.conf import settings

def get_puzzle(puzzle_type, puzzle_date):

    url = f"http://www.puzzles.grosse.is-a-geek.com/images/gog/puz/{puzzle_type}/{puzzle_type}{puzzle_date}puz.png"
    
    # Pull the puzzle from the database
    with psycopg.connect(settings.PG_CONNECTION) as conn:
        with conn.cursor() as cur:
            cur.execute(f"SELECT * FROM {puzzle_type} WHERE puzzle_url = '{url}';")
            puzzle = cur.fetchone()
            if puzzle is None:
                cur.execute(f"SELECT * FROM {puzzle_type} ORDER BY puzzle_name DESC LIMIT 1;")
                puzzle = cur.fetchone()

    return puzzle


def get_generated_puzzle(puzzle_type, seed):
    """Pull a generated puzzle straight from the puzzle database."""

    with psycopg.connect(settings.PG_CONNECTION) as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"SELECT * FROM {puzzle_type}_generated WHERE puzzle_name = %s;",
                (f"{puzzle_type}{seed}",),
            )
            return cur.fetchone()
