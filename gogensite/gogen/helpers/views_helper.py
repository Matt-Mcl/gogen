from django.shortcuts import render, redirect
from django.conf import settings
from django.http import HttpResponseNotFound
from copy import deepcopy
from datetime import datetime, date, timedelta
import re
import psycopg

from ..models import *


def get_user_settings(request):

    user_settings = Settings(user=None)

    if request.user.id is not None:
        # If user hasn't got a Settings model attached to them, create one
        if not getattr(request.user, "settings", False):
            new_settings = Settings(user=request.user)
            new_settings.save()

        user_settings = request.user.settings

    return user_settings


def get_puzzle_log(puzzle_type, puzzle_date, request, notes, user_settings):

    user_puzzle_log = PuzzleLog.objects.filter(puzzle_type=puzzle_type, puzzle_date=puzzle_date, user=request.user)

    # If notes are currently disabled, update variable to use what's in the database
    # Prevents notes being removed when notes are disabled
    if not user_settings.notes_enabled:
        if user_puzzle_log.count() > 0:
            notes = user_puzzle_log[0].notes
    
    return user_puzzle_log, notes


def get_next_puzzle(request, puzzle_type, puzzle_date):
    
    # Find the next puzzle the user has not solved
    next_puzzle_url = None

    if request.user.is_authenticated:
        next_puzzle = None
        puzzle_logs = PuzzleLog.objects.filter(puzzle_type=puzzle_type, user=request.user, puzzle_date__lt=puzzle_date).order_by('-puzzle_date')
        last_complete = None
        last_date = puzzle_date
        for pl in puzzle_logs:
            if pl.puzzle_date != (datetime.strptime(last_date, "%Y%m%d") - timedelta(days=1)).strftime('%Y%m%d'):
                next_puzzle = (datetime.strptime(last_date, "%Y%m%d") - timedelta(days=1)).strftime('%Y%m%d')
                break
            # If incomplete
            if pl.status == PuzzleLog.STATUS_CHOICES[1][0]:
                next_puzzle = pl.puzzle_date
                break
            # If complete
            if pl.status == PuzzleLog.STATUS_CHOICES[0][0]:
                last_complete = pl.puzzle_date

            last_date = pl.puzzle_date
        
        if next_puzzle is None:
            if last_complete is None:
                next_puzzle = (datetime.strptime(puzzle_date, "%Y%m%d") - timedelta(days=1)).strftime('%Y%m%d')
            else:
                next_puzzle = (datetime.strptime(last_complete, "%Y%m%d") - timedelta(days=1)).strftime('%Y%m%d')
        
        next_puzzle_url = f"/{puzzle_type}_archive{next_puzzle}"

        if next_puzzle == "20190119":
            next_puzzle_url = None

    return next_puzzle_url


def load_saved_progress(request, puzzle_type, puzzle_date, board):
    """Overlay whatever the user has already filled in on top of a fresh board."""

    notes = ""
    placeholders = [["" for _ in range(5)] for _ in range(5)]
    navbar_template = 'registration/logged_out_base.html'

    if request.user.id is not None:
        navbar_template = 'registration/logged_in_base.html'

        user_puzzle_log = PuzzleLog.objects.filter(puzzle_type=puzzle_type, puzzle_date=puzzle_date, user=request.user)

        # If user has already filled some letters out, add them to the board
        if user_puzzle_log.count() > 0:
            board = user_puzzle_log[0].board
            placeholders = user_puzzle_log[0].placeholders
            notes = user_puzzle_log[0].notes

    return board, placeholders, notes, navbar_template


# Which letters get a hint line, per the user's setting. Gogen has no Z, and
# the notes feature counts Y as a vowel.
VOWEL_LETTERS = "AEIOUY"
ALL_LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXY"

HINT_LETTERS = {
    'V': VOWEL_LETTERS,
    'A': ALL_LETTERS,
}


def apply_notes_settings(words, notes, user_settings):
    """Seed the notes box from the user's preset and hint settings."""

    # If user has a notes preset and puzzle hasn't been attempted yet, set notes as the preset
    if user_settings.preset_notes is not None and notes == "":
        notes = user_settings.preset_notes.template

    # If the user has hints enabled, add them to the notes
    hint_letters = HINT_LETTERS.get(user_settings.fill_hints, "")

    if hint_letters:
        # If notes are empty or the preset notes are unchanged, add the hints
        if notes == "" or (user_settings.preset_notes is not None and notes == user_settings.preset_notes.template):
            for hint_letter in hint_letters:
                added_hints = []
                for word in words:
                    for i, letter in enumerate(word):
                        if letter.upper() != hint_letter:
                            # If the letter is not already in the notes and the letter before or after it is the hint letter
                            if letter.upper() not in added_hints and ((i > 0 and word[i-1].upper() == hint_letter) or (i < len(word)-1 and word[i+1].upper() == hint_letter)):
                                added_hints.append(letter.upper())
                                # Add the hint to the notes if it's not already there, otherwise add to the existing hint
                                if f"{hint_letter}: " not in notes:
                                    notes += f"{hint_letter}: {letter.upper()}\n"
                                else:
                                    notes = re.sub(f"{hint_letter}: ", f"{hint_letter}: {letter.upper()}", notes)

    return notes


def get_puzzle(request, puzzle_type, puzzle_date, page_heading):

    url = f"http://www.puzzles.grosse.is-a-geek.com/images/gog/puz/{puzzle_type}/{puzzle_type}{puzzle_date}puz.png"
    puzzle_count = 0

    # Pull the puzzle from the database + get the count for the puzzle type
    with psycopg.connect(settings.PG_CONNECTION) as conn:
        with conn.cursor() as cur:
            cur.execute(f"SELECT COUNT(*) FROM {puzzle_type};")
            puzzle_count = cur.fetchone()[0]

            cur.execute(f"SELECT * FROM {puzzle_type} WHERE puzzle_url = '{url}';")
            puzzle = cur.fetchone()
            if puzzle is None:
                cur.execute(f"SELECT * FROM {puzzle_type} ORDER BY puzzle_name DESC LIMIT 1;")
                puzzle = cur.fetchone()
                page_heading = puzzle[0].capitalize()

    url = puzzle[1]
    words = puzzle[3]
    board = puzzle[4]

    board, placeholders, notes, navbar_template = load_saved_progress(request, puzzle_type, puzzle_date, board)

    user_settings = get_user_settings(request)
    notes = apply_notes_settings(words, notes, user_settings)

    return render(
        request=request,
        template_name='gogen/puzzle.html',
        context={
            'url': url,
            'words': words,
            'board': board,
            'placeholders': placeholders,
            'notes': notes,
            'page_heading': page_heading,
            'navbar_template': navbar_template,
            'logged_in': request.user.id is not None,
            'puzzle_count': puzzle_count * 3,
            'next_puzzle_url': get_next_puzzle(request, puzzle_type, puzzle_date),
            'notes_enabled': user_settings.notes_enabled,
        }
    )


def post_puzzle(request, page_heading):
    post_items = list(request.POST.items())
    # Create 2D array of placeholders
    placeholders = [["" for _ in range(5)] for _ in range(5)] 
    for i, v in enumerate(post_items.pop()[1].split(',')):
        placeholders[i//5][i%5] = v

    notes = post_items.pop()[1]
    user_settings = get_user_settings(request)

    # Get URL and date of the puzzle
    url = post_items[1][1]

    pattern = re.compile(r'^(http:\/\/www\.puzzles\.grosse\.is-a-geek\.com\/images\/gog\/puz\/)(uber|ultra|hyper)(\/)(uber|ultra|hyper)([0-9]{8})(puz\.png)$')

    if not pattern.match(url):
        return HttpResponseNotFound("URL has been modified.")

    puzzle_type = url.split('/')[-1][:-15]
    puzzle_date = url.split('/')[-1][-15:-7]
    puzzle_count = 0

    # Pull the puzzle from the database + get the count for the puzzle type
    with psycopg.connect(settings.PG_CONNECTION) as conn:
        with conn.cursor() as cur:
            cur.execute(f"SELECT COUNT(*) FROM {puzzle_type};")
            puzzle_count = cur.fetchone()[0]

            cur.execute(f"SELECT * FROM {puzzle_type} WHERE puzzle_url = '{url}';")

            puzzle = cur.fetchone()

            if puzzle is None:
                return HttpResponseNotFound("URL has been modified: Puzzle not found in database.")

            solution_board = puzzle[5]

    url = puzzle[1]
    words = puzzle[3]
    navbar_template = 'registration/logged_out_base.html'
    complete = False
    mistake = False

    # Create copy of solution board
    letters = deepcopy(solution_board)

    # Remove button response from post items
    if post_items[-1][0] == "submit_button":
        post_items.pop()
    
    # Copy the letters the user put in over the solution board
    # If the letters are wrong, their board will now be different to the solution board
    for item in post_items[2:]:
        letters[int(item[0][0])][int(item[0][1])] = item[1][:1].upper()

    # If the solution and the users board still match
    if letters == solution_board:
        complete = True
        # If logged in save the puzzlelog to the database
        if request.user.id is not None:
            navbar_template = 'registration/logged_in_base.html'
            user_puzzle_log, notes = get_puzzle_log(puzzle_type, puzzle_date, request, notes, user_settings)
            # Create new record for puzzlelog completion if it doesn't exist
            if user_puzzle_log.count() == 0:
                puzzle_log = PuzzleLog(puzzle_type=puzzle_type, puzzle_date=puzzle_date, status='C', board=letters, placeholders=placeholders, notes=notes, user=request.user)
                puzzle_log.save()
            # If record already exists, mark as completed
            else:
                user_puzzle_log.update(status='C', board=letters, placeholders=placeholders, notes=notes)
    else:
        mistake = True
        # Loop through each cell in the board and flag user changes with an asterisk
        for i in range(0, 5): # TODO: Check if this can more efficient
            for j, v in enumerate(zip(letters[i], puzzle[4][i])):
                if v[0] != v[1] or v[0] == "":
                    letters[i][j] = f"*{letters[i][j]}"

        # If logged in save the puzzlelog to the database
        if request.user.id is not None:
            navbar_template = 'registration/logged_in_base.html'
            user_puzzle_log, notes = get_puzzle_log(puzzle_type, puzzle_date, request, notes, user_settings)
            # Create new record for incomplete puzzlelog if it doesn't exist
            if user_puzzle_log.count() == 0:
                puzzle_log = PuzzleLog(puzzle_type=puzzle_type, puzzle_date=puzzle_date, status='I', board=letters, placeholders=placeholders, notes=notes, user=request.user)
                puzzle_log.save()
            # If record already exists, updates the board with the new letters the user put in
            else:
                if user_puzzle_log[0].status == 'C':
                    mistake = False
                    complete = True
                    placeholders = user_puzzle_log[0].placeholders
                    letters = user_puzzle_log[0].board
                    notes = user_puzzle_log[0].notes
                else:
                    user_puzzle_log.update(board=letters, placeholders=placeholders, notes=notes)

    return render(
        request=request,
        template_name='gogen/puzzle.html',
        context={
            'url': url,
            'words': words,
            'board': letters,
            'placeholders': placeholders,
            'notes': notes,
            'mistake': mistake,
            'complete': complete,
            'page_heading': page_heading,
            'navbar_template': navbar_template,
            'puzzle_count': puzzle_count * 3,
            'logged_in': request.user.id is not None,
            'next_puzzle_url': get_next_puzzle(request, puzzle_type, puzzle_date),
            'notes_enabled': user_settings.notes_enabled
        }
    )


# Puzzles built by gogenmaker rather than scraped from the archive. Each type
# lives in its own table and is addressed by generation seed, so /ultra1 is
# ultra seed 1. The stored puzzle_type keeps their progress separate from the
# archive's, so seed 1 never collides with a date.
GENERATED_TYPES = ("uber", "ultra", "hyper")


def generated_table(puzzle_type):
    return f"{puzzle_type}_generated"


def generated_log_type(puzzle_type):
    return f"{puzzle_type}_generated"


# The home page walks the generated uber seeds, one per day
DAILY_TYPE = "uber"
DAILY_EPOCH = date(2026, 8, 8)  # the day seed 1 is the daily puzzle

# The address of a generated puzzle, as stored in puzzle_url and posted back
GENERATED_URL = re.compile(r'^/(uber|ultra|hyper)([1-9]\d*)$')


def daily_seed(today=None):
    """Which generated seed is today's puzzle."""

    today = today or datetime.now().date()

    return max(1, (today - DAILY_EPOCH).days + 1)


def existing_generated_tables(conn):
    """Which of the generated tables have actually been created."""

    names = [generated_table(puzzle_type) for puzzle_type in GENERATED_TYPES]
    rows = conn.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_name = ANY(%s);",
        (names,),
    ).fetchall()

    return [name for (name,) in rows]


def generated_puzzle_total(conn):
    """How many generated puzzles exist across every type.

    Which tables exist is looked up first rather than catching UndefinedTable
    per table: one missing table would abort the whole transaction.
    """

    tables = existing_generated_tables(conn)
    if not tables:
        return 0

    # The table names come from the GENERATED_TYPES whitelist, never user input
    counts = " + ".join(f"(SELECT COUNT(*) FROM {table})" for table in tables)

    return conn.execute(f"SELECT {counts};").fetchone()[0]


def fetch_generated_puzzle(puzzle_type, seed):
    """Return (puzzle_row, total generated puzzles). The row is None if that seed is absent."""

    table = generated_table(puzzle_type)

    with psycopg.connect(settings.PG_CONNECTION) as conn:
        puzzle = None

        if table in existing_generated_tables(conn):
            puzzle = conn.execute(
                f"SELECT * FROM {table} WHERE puzzle_name = %s;", (f"{puzzle_type}{seed}",)
            ).fetchone()

        return puzzle, generated_puzzle_total(conn)


def generated_seeds(puzzle_type):
    """Every stored seed of this type, lowest first.

    The seeds are parsed and sorted here rather than in SQL because ordering
    puzzle_name is lexicographic, which puts uber10 before uber2.
    """

    table = generated_table(puzzle_type)

    try:
        with psycopg.connect(settings.PG_CONNECTION) as conn:
            rows = conn.execute(f"SELECT puzzle_name FROM {table};").fetchall()
    except psycopg.errors.UndefinedTable:
        return []

    seeds = (name[len(puzzle_type):] for (name,) in rows)

    return sorted(int(seed) for seed in seeds if seed.isdigit())


def completed_generated_seeds(request, puzzle_type):
    """The seeds of this type the user has finished. Empty when logged out."""

    if not request.user.is_authenticated:
        return set()

    puzzle_dates = PuzzleLog.objects.filter(
        user=request.user,
        puzzle_type=generated_log_type(puzzle_type),
        status=PuzzleLog.STATUS_CHOICES[0][0],
    ).values_list('puzzle_date', flat=True)

    # puzzle_date is a free text field, so only take the ones holding a seed
    return {int(d) for d in puzzle_dates if d.isdigit()}


def earliest_incomplete_seed(request, puzzle_type, seeds=None):
    """The first seed the user has not completed.

    Puzzles live in the puzzle database and progress lives in Django's, so the
    two are matched up here rather than in a query. Someone who has finished
    everything gets their latest puzzle back instead of nothing.
    """

    seeds = generated_seeds(puzzle_type) if seeds is None else seeds
    if not seeds:
        return None

    completed = completed_generated_seeds(request, puzzle_type)

    for seed in seeds:
        if seed not in completed:
            return seed

    return seeds[-1]


def redirect_to_earliest_incomplete(request, puzzle_type, exclude_seed=None):
    """Send the user to their earliest unsolved puzzle of this type.

    Used both by the difficulty links and by requests for a seed that was
    never generated. `exclude_seed` guards against redirecting to the very
    seed we could not find, which would loop.
    """

    target = earliest_incomplete_seed(request, puzzle_type)

    if target is None or target == exclude_seed:
        return HttpResponseNotFound(f"No {puzzle_type} puzzles are available.")

    return redirect(f"/{puzzle_type}{target}")


def get_next_generated_url(request, puzzle_type, seed, is_daily=False):
    """Where the Next button points.

    Logged out there is no Next at all. On the daily puzzle it goes back to
    the earliest puzzle still unsolved, so nothing gets left behind. Anywhere
    else it steps forward one seed, letting a hard puzzle be skipped.
    """

    if not request.user.is_authenticated:
        return None

    seeds = generated_seeds(puzzle_type)
    if not seeds:
        return None

    if is_daily or (seed + 1) not in set(seeds):
        target = earliest_incomplete_seed(request, puzzle_type, seeds=seeds)
    else:
        target = seed + 1

    # Nothing to move on to, so the button stays disabled rather than self-linking
    if target is None or target == seed:
        return None

    return f"/{puzzle_type}{target}"


def seed_from_posted_url(request, puzzle_type):
    """The seed the form was rendered from, or None.

    The daily page posts back to "/", so without this a submission made just
    after midnight would be marked against the following day's puzzle.
    """

    match = GENERATED_URL.match(request.POST.get("url", ""))

    if match and match.group(1) == puzzle_type:
        return int(match.group(2))

    return None


def apply_submission(post_items, solution_board):
    """Copy the letters the user entered over a copy of the solution.

    Given cells are not form inputs, so they are never posted back and keep
    their solved value. If the user's letters are wrong, the board that comes
    out no longer matches the solution.
    """

    letters = deepcopy(solution_board)

    for name, value in post_items:
        if name.endswith("_board_letter"):
            letters[int(name[0])][int(name[1])] = value[:1].upper()

    return letters


def get_generated_puzzle(request, puzzle_type, seed, page_heading, is_daily=False):

    puzzle, puzzle_count = fetch_generated_puzzle(puzzle_type, seed)

    if puzzle is None:
        return redirect_to_earliest_incomplete(request, puzzle_type, exclude_seed=seed)

    url = puzzle[1]
    words = puzzle[3]
    board = puzzle[4]

    board, placeholders, notes, navbar_template = load_saved_progress(request, generated_log_type(puzzle_type), str(seed), board)

    user_settings = get_user_settings(request)
    notes = apply_notes_settings(words, notes, user_settings)

    return render(
        request=request,
        template_name='gogen/puzzle.html',
        context={
            'url': url,
            'words': words,
            'board': board,
            'placeholders': placeholders,
            'notes': notes,
            'page_heading': page_heading,
            'navbar_template': navbar_template,
            'logged_in': request.user.id is not None,
            'puzzle_count': puzzle_count,
            'next_puzzle_url': get_next_generated_url(request, puzzle_type, seed, is_daily),
            'notes_enabled': user_settings.notes_enabled,
        }
    )


def post_generated_puzzle(request, puzzle_type, seed, page_heading, is_daily=False):

    puzzle, puzzle_count = fetch_generated_puzzle(puzzle_type, seed)

    if puzzle is None:
        return redirect_to_earliest_incomplete(request, puzzle_type, exclude_seed=seed)

    url = puzzle[1]
    words = puzzle[3]
    solution_board = puzzle[5]

    post_items = list(request.POST.items())

    # Create 2D array of placeholders
    placeholders = [["" for _ in range(5)] for _ in range(5)]
    for i, v in enumerate(post_items.pop()[1].split(',')):
        placeholders[i//5][i%5] = v

    notes = post_items.pop()[1]

    user_settings = get_user_settings(request)
    navbar_template = 'registration/logged_in_base.html' if request.user.id is not None else 'registration/logged_out_base.html'

    letters = apply_submission(post_items, solution_board)
    complete = letters == solution_board
    mistake = not complete

    if mistake:
        # Loop through each cell in the board and flag user changes with an asterisk
        for i in range(0, 5):
            for j, v in enumerate(zip(letters[i], puzzle[4][i])):
                if v[0] != v[1] or v[0] == "":
                    letters[i][j] = f"*{letters[i][j]}"

    # If logged in save the puzzlelog to the database
    if request.user.id is not None:
        user_puzzle_log, notes = get_puzzle_log(generated_log_type(puzzle_type), str(seed), request, notes, user_settings)
        status = 'C' if complete else 'I'

        if user_puzzle_log.count() == 0:
            puzzle_log = PuzzleLog(puzzle_type=generated_log_type(puzzle_type), puzzle_date=str(seed), status=status, board=letters, placeholders=placeholders, notes=notes, user=request.user)
            puzzle_log.save()
        # Once a puzzle is complete it stays complete, so show the solved board again
        elif mistake and user_puzzle_log[0].status == 'C':
            mistake = False
            complete = True
            placeholders = user_puzzle_log[0].placeholders
            letters = user_puzzle_log[0].board
            notes = user_puzzle_log[0].notes
        else:
            user_puzzle_log.update(status=status, board=letters, placeholders=placeholders, notes=notes)

    return render(
        request=request,
        template_name='gogen/puzzle.html',
        context={
            'url': url,
            'words': words,
            'board': letters,
            'placeholders': placeholders,
            'notes': notes,
            'mistake': mistake,
            'complete': complete,
            'page_heading': page_heading,
            'navbar_template': navbar_template,
            'puzzle_count': puzzle_count,
            'logged_in': request.user.id is not None,
            'next_puzzle_url': get_next_generated_url(request, puzzle_type, seed, is_daily),
            'notes_enabled': user_settings.notes_enabled,
        }
    )
