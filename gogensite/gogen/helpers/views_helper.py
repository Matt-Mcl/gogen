from django.shortcuts import render
from django.conf import settings
from django.http import HttpResponseNotFound
from copy import deepcopy
from datetime import datetime, timedelta
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
        
        next_puzzle_url = f"/{puzzle_type}{next_puzzle}"

        if next_puzzle == "20190119":
            next_puzzle_url = None

    return next_puzzle_url


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
    notes = ""
    placeholders = [["" for _ in range(5)] for _ in range(5)]
    navbar_template = 'registration/logged_out_base.html'

    # If logged in, get the user's puzzlelog data for the given puzzle
    if request.user.id is not None:
        navbar_template = 'registration/logged_in_base.html'

        user_puzzle_log = PuzzleLog.objects.filter(puzzle_type=puzzle_type, puzzle_date=puzzle_date, user=request.user)
        
        # If user has already filled some letters out, add them to the board
        if user_puzzle_log.count() > 0:
            board = user_puzzle_log[0].board
            placeholders = user_puzzle_log[0].placeholders
            notes = user_puzzle_log[0].notes

    user_settings = get_user_settings(request)

    # If user has a notes preset and puzzle hasn't been attempted yet, set notes as the preset
    if user_settings.preset_notes is not None and notes == "":
        notes = user_settings.preset_notes.template

    # If the user has fill vowel hints enabled, add them to the notes
    if user_settings.fill_vowels_enabled:
        # If notes are empty or the preset notes are unchanged, add vowel hints
        if notes == "" or (user_settings.preset_notes is not None and notes == user_settings.preset_notes.template):
            for vowel in ['A', 'E', 'I', 'O', 'U', 'Y']:
                added_hints = []
                for word in words:
                    for i, letter in enumerate(word):
                        if letter.upper() != vowel:
                            # If the letter is not already in the notes and the letter before or after it is a vowel
                            if letter.upper() not in added_hints and ((i > 0 and word[i-1].upper() == vowel) or (i < len(word)-1 and word[i+1].upper() == vowel)):
                                added_hints.append(letter.upper())
                                # Add the hint to the notes if it's not already there, otherwise add to the existing hint
                                if f"{vowel}: " not in notes:
                                    notes += f"{vowel}: {letter.upper()}\n"
                                else:
                                    notes = re.sub(f"{vowel}: ", f"{vowel}: {letter.upper()}", notes)

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
