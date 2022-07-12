from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, authenticate
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from datetime import datetime, timedelta
from django.conf import settings
import psycopg

from .models import *
from .helpers import views_helper


def daily_view(request):

    if request.method == "GET":
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
        return views_helper.get_puzzle(request, "uber", yesterday, "Daily Uber")

    if request.method == "POST":
        return views_helper.post_puzzle(request, "Daily Uber")


@login_required
def puzzle_view(request, puzzle_date, puzzle_type):

    if request.method == "GET":
        return views_helper.get_puzzle(request, puzzle_type, puzzle_date, f"{puzzle_type}{puzzle_date}")

    if request.method == "POST":
        return views_helper.post_puzzle(request, f"{puzzle_type}{puzzle_date}")


@login_required
def puzzle_list_view(request):

    if request.method == "GET":

        puzzle_types = ["uber", "ultra", "hyper"]
        puzzles = []

        this_page = request.GET.get("page", 1)

        for puzzle_type in puzzle_types:
            puzzle_type_array = []
            # Get all puzzles by type
            with psycopg.connect(settings.PG_CONNECTION) as conn:
                with conn.cursor() as cur:
                    cur.execute(f"SELECT puzzle_name FROM {puzzle_type} ORDER BY puzzle_name DESC")
                    db_puzzles = cur.fetchall()

            # Paginate to keep 15 per page
            paginated_puzzles = Paginator(db_puzzles, 15)

            # Validate invalid page numbers
            try:
                page_puzzles = paginated_puzzles.page(this_page)
            except (PageNotAnInteger, EmptyPage):
                this_page = "1"
                page_puzzles = paginated_puzzles.page(1)

            # Check if the user has completed the puzzle
            for puzzle in page_puzzles:
                puzzle_type = puzzle[0][:-8]
                puzzle_date = puzzle[0][-8:]
                user_puzzle_log = PuzzleLog.objects.filter(puzzle_type=puzzle_type, puzzle_date=puzzle_date, user=request.user)

                if user_puzzle_log.count() > 0:
                    puzzle_type_array.append( (puzzle[0], user_puzzle_log[0].status) )
                else:
                    puzzle_type_array.append( (puzzle[0], 'I') )

            puzzles.append( (puzzle_type.capitalize(), puzzle_type_array) )

        lower_range = range(1, paginated_puzzles.num_pages + 1)
        upper_range = None
        # If greater that 20 pages split into first and last 10
        if paginated_puzzles.num_pages > 20:
            lower_range = range(1, 11)
            upper_range = range(paginated_puzzles.num_pages - 9, paginated_puzzles.num_pages + 1)
        # Scroll numbers if page past 5
        if int(this_page) > 5 and paginated_puzzles.num_pages - int(this_page) > 8:
            lower_range = range(int(this_page) - 4, min(11 + int(this_page) - 5, paginated_puzzles.num_pages - 9))

        return render(
            request=request,
            template_name="gogen/puzzle_list.html",
            context={
                'page_puzzles': page_puzzles,
                'puzzles': puzzles,
                'lower_range': lower_range,
                'upper_range': upper_range
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
