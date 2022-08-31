from django.shortcuts import render
from django.conf import settings
from django.http import HttpResponseNotFound
from copy import deepcopy
import psycopg

from ..models import *

def get_puzzle(request, puzzle_type, puzzle_date, page_heading):

    url = f"http://www.puzzles.grosse.is-a-geek.com/images/gog/puz/{puzzle_type}/{puzzle_type}{puzzle_date}puz.png"
    
    # Pull the puzzle from the database
    with psycopg.connect(settings.PG_CONNECTION) as conn:
        with conn.cursor() as cur:
            cur.execute(f"SELECT * FROM {puzzle_type} WHERE puzzle_url = '{url}';")
            puzzle = cur.fetchone()

    url = puzzle[1]
    words = puzzle[3]
    board = puzzle[4]
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

    return render(
        request=request,
        template_name='gogen/puzzle.html',
        context={
            'url': url,
            'words': words,
            'board': board,
            'placeholders': placeholders,
            'page_heading': page_heading,
            'navbar_template': navbar_template
        }
    )


def post_puzzle(request, page_heading):
    post_items = list(request.POST.items())
    # Create 2D array of placeholders
    placeholders = [["" for _ in range(5)] for _ in range(5)] 
    for i, v in enumerate(post_items.pop()[1].split(',')):
        placeholders[i//5][i%5] = v

    # Get URL and date of the puzzle
    url = post_items[1][1]
    puzzle_type = url.split('/')[-1][:-15]
    puzzle_date = url.split('/')[-1][-15:-7]

    if puzzle_type not in ["uber", "ultra", "hyper"]:
        return HttpResponseNotFound("URL has been modified: Invalid puzzle type in URL.")

    # Pull the puzzle from the database
    with psycopg.connect(settings.PG_CONNECTION) as conn:
        with conn.cursor() as cur:
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
        letters[int(item[0][0])][int(item[0][1])] = item[1]

    # If the solution and the users board still match
    if letters == solution_board:
        complete = True

        # If logged in save the puzzlelog to the database
        if request.user.id is not None:
            navbar_template = 'registration/logged_in_base.html'
            user_puzzle_log = PuzzleLog.objects.filter(puzzle_type=puzzle_type, puzzle_date=puzzle_date, user=request.user)
            # Create new record for puzzlelog completion if it doesn't exist
            if user_puzzle_log.count() == 0:
                puzzle_log = PuzzleLog(puzzle_type=puzzle_type, puzzle_date=puzzle_date, status='C', board=letters, placeholders=placeholders, user=request.user)
                puzzle_log.save()
            # If record already exists, mark as completed
            else:
                user_puzzle_log.update(status='C', board=letters, placeholders=placeholders)
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
            user_puzzle_log = PuzzleLog.objects.filter(puzzle_type=puzzle_type, puzzle_date=puzzle_date, user=request.user)
            # Create new record for incomplete puzzlelog if it doesn't exist
            if user_puzzle_log.count() == 0:
                puzzle_log = PuzzleLog(puzzle_type=puzzle_type, puzzle_date=puzzle_date, status='I', board=letters, placeholders=placeholders, user=request.user)
                puzzle_log.save()
            # If record already exists, updates the board with the new letters the user put in
            else:
                user_puzzle_log.update(board=letters, placeholders=placeholders)

    return render(
        request=request,
        template_name='gogen/puzzle.html',
        context={
            'url': url,
            'words': words,
            'board': letters,
            'placeholders': placeholders,
            'mistake': mistake,
            'complete': complete,
            'page_heading': page_heading,
            'navbar_template': navbar_template
        }
    )
