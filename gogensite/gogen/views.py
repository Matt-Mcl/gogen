from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, authenticate
from django.http import HttpResponse
from django.conf import settings
from datetime import datetime, timedelta
from copy import deepcopy
import psycopg

from .models import *

def daily_view(request):

    if request.method == "GET":

        # Get yesterday's gogen URL
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
        url = f"http://www.puzzles.grosse.is-a-geek.com/images/gog/puz/uber/uber{yesterday}puz.png"
        
        # Pull the puzzle from the database
        with psycopg.connect(settings.PG_CONNECTION) as conn:
            with conn.cursor() as cur:
                cur.execute(f"SELECT * FROM uber WHERE puzzle_url = '{url}';")
                daily_uber = cur.fetchone()

        url = daily_uber[0]
        words = daily_uber[2]
        board = daily_uber[3]
        navbar_template = 'registration/logged_out_base.html'

        # If logged in, get the user's puzzlelog data for the given puzzle
        if request.user.id is not None:
            navbar_template = 'registration/logged_in_base.html'

            user_puzzle_log = PuzzleLog.objects.filter(puzzle_type='uber', puzzle_date=yesterday, user=request.user)
            
            # If user has already filled some letters out, add them to the board
            if user_puzzle_log.count() > 0:
                board = user_puzzle_log[0].board

        return render(
            request=request,
            template_name='gogen/puzzle.html',
            context={
                'url': daily_uber[0],
                'words': words,
                'board': board,
                'page_heading': 'Daily Uber',
                'navbar_template': navbar_template
            }
        )

    if request.method == "POST":

        # Get URL and date of the puzzle
        url = list(request.POST.items())[1][1]
        puzzle_date = url.split('/')[-1][4:12]

        # Pull the puzzle from the database
        with psycopg.connect(settings.PG_CONNECTION) as conn:
            with conn.cursor() as cur:
                cur.execute(f"SELECT * FROM uber WHERE puzzle_url = '{url}';")

                daily_uber = cur.fetchone()

                solution_board = daily_uber[4]

        url = daily_uber[0]
        words = daily_uber[2]
        board = daily_uber[3]
        navbar_template = 'registration/logged_out_base.html'
        complete = False
        mistake = False

        # Create copy of solution board
        letters = deepcopy(solution_board)

        # Get the letters the user filled out from the "board form"
        for item in list(request.POST.items())[2:]:
            letters[int(item[0][0])][int(item[0][1])] = item[1]

        # If the solution and the users board still match
        if letters == solution_board:
            complete = True

            # If logged in save the puzzlelog to the database
            if request.user.id is not None:
                navbar_template = 'registration/logged_in_base.html'
                user_puzzle_log = PuzzleLog.objects.filter(puzzle_type='uber', puzzle_date=puzzle_date, user=request.user)
                # Create new record for puzzlelog completion if it doesn't exist
                if user_puzzle_log.count() == 0:
                    puzzle_log = PuzzleLog(puzzle_type='uber', puzzle_date=puzzle_date, status='C', board=letters, user=request.user)
                    puzzle_log.save()
                # If record already exists, mark as completed
                else:
                    user_puzzle_log.update(status='C', board=letters)

        else:
            mistake = True
            # Loop through each cell in the board and flag user changes with an asterisk
            for i in range(0, 5):
                for j, v in enumerate(zip(letters[i], daily_uber[3][i])):
                    if v[0] != v[1] or v[0] == "":
                        letters[i][j] = f"*{letters[i][j]}"

            # If logged in save the puzzlelog to the database
            if request.user.id is not None:
                navbar_template = 'registration/logged_in_base.html'
                user_puzzle_log = PuzzleLog.objects.filter(puzzle_type='uber', puzzle_date=puzzle_date, user=request.user)
                # Create new record for incomplete puzzlelog if it doesn't exist
                if user_puzzle_log.count() == 0:
                    puzzle_log = PuzzleLog(puzzle_type='uber', puzzle_date=puzzle_date, status='I', board=letters, user=request.user)
                    puzzle_log.save()
                # If puzzle already complete, tell the user
                elif user_puzzle_log[0].status == 'C':
                    return HttpResponse("Puzzle already completed!")

                else:
                    user_puzzle_log.update(board=letters)

        return render(
            request=request,
            template_name='gogen/puzzle.html',
            context={
                'url': url,
                'words': words,
                'board': letters,
                'mistake': mistake,
                'complete': complete,
                'page_heading': 'Daily Uber',
                'navbar_template': navbar_template
            }
        )


@login_required
def puzzle_list_view(request):

    if request.method == "GET":
        pass


@login_required
def puzzle_view(request, puzzle_date, puzzle_type):

    if request.method == "GET":
        url = f"http://www.puzzles.grosse.is-a-geek.com/images/gog/puz/{puzzle_type}/{puzzle_type}{puzzle_date}puz.png"
        
        with psycopg.connect(settings.PG_CONNECTION) as conn:
            with conn.cursor() as cur:
                cur.execute(f"SELECT * FROM {puzzle_type} WHERE puzzle_url = '{url}';")

                puzzle = cur.fetchone()

                if puzzle is None:
                    return HttpResponse("Puzzle does not exist", status=404)

                return render(
                    request=request,
                    template_name='gogen/puzzle.html',
                    context={
                        'url': puzzle[0],
                        'words': puzzle[2],
                        'board': puzzle[3],
                        'page_heading': f"{puzzle_type}{puzzle_date}"
                    }
                )


def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username = username, password = password)
            login(request, user)
            return redirect('/')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})
