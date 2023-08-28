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
        today = datetime.now().strftime('%Y%m%d')
        return views_helper.get_puzzle(request, "uber", today, "Daily Uber")

    if request.method == "POST":
        return views_helper.post_puzzle(request, "Daily Uber")


@login_required
def puzzle_view(request, puzzle_date, puzzle_type):

    if request.method == "GET":
        return views_helper.get_puzzle(request, puzzle_type, puzzle_date, f"{puzzle_type.capitalize()}{puzzle_date}")

    if request.method == "POST":
        return views_helper.post_puzzle(request, f"{puzzle_type.capitalize()}{puzzle_date}")


@login_required
def puzzle_list_view(request, puzzle_type):

    if request.method == "GET":
        puzzles = []

        this_page = request.GET.get("page", 1)

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
            return redirect(f"/puzzlelist/{puzzle_type}")

        # Check if the user has completed the puzzle
        for puzzle in page_puzzles:
            p_type = puzzle[0][:-8]
            p_date = puzzle[0][-8:]
            user_puzzle_log = PuzzleLog.objects.filter(puzzle_type=p_type, puzzle_date=p_date, user=request.user)

            if user_puzzle_log.count() > 0 and user_puzzle_log[0].status == PuzzleLog.STATUS_CHOICES[0][0]:
                puzzles.append( (puzzle[0], "✓") )
            else:
                puzzles.append( (puzzle[0], "-") )

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
                'puzzle_type': puzzle_type.capitalize(),
                'puzzles': puzzles,
                'lower_range': lower_range,
                'upper_range': upper_range,
                'page_heading': "Puzzle List"
            }
        )


@login_required
def leaderboard_view(request):

    users_and_scores = []

    for user in User.objects.all():
        if not user.is_superuser:
            user_puzzle_logs = PuzzleLog.objects.filter(user=user, status='C')
            uber_count = user_puzzle_logs.filter(puzzle_type='uber').count()
            ultra_count = user_puzzle_logs.filter(puzzle_type='ultra').count()
            hyper_count = user_puzzle_logs.filter(puzzle_type='hyper').count()
            users_and_scores.append( (user.username, uber_count, ultra_count, hyper_count, user_puzzle_logs.count()) )
    
    users_and_scores.sort(key=lambda x: x[1], reverse=True)

    return render(
        request=request,
        template_name="gogen/leaderboard.html",
        context={
            'users_and_scores': users_and_scores,
            'page_heading': "Gogen Leaderboard",
        }
    )


@login_required
def settings_view(request):

    if not getattr(request.user, "settings", False):
        new_settings = Settings(user=request.user)
        new_settings.save()

    user_settings = request.user.settings

    if request.method == "POST":
        if request.POST.get("notes_enabled") == "on":
            user_settings.notes_enabled = True
        else:
            user_settings.notes_enabled = False
        
        # If a notes preset is selected
        notes_preset = [x for x in request.POST.keys() if "notes_preset" in x]

        if notes_preset:
            notes_preset = notes_preset[0]
            user_settings.preset_notes = NoteTemplate.objects.get(id=notes_preset[-1])
        else:
            user_settings.preset_notes = None

    user_settings.save()

    presets = NoteTemplate.objects.all()

    return render(
        request=request,
        template_name="gogen/settings.html",
        context={
            'notes_value': user_settings.notes_enabled,
            'presets': presets,
            'selected_preset': user_settings.preset_notes,
            'page_heading': "Gogen Settings",
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
