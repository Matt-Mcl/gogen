from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, authenticate

from .models import *
from .helpers import views_helper


def daily_view(request):
    """Today's puzzle: a generated uber whose seed advances one per day."""

    puzzle_type = views_helper.DAILY_TYPE
    seed = views_helper.daily_seed()
    page_heading = "Daily Uber"

    if request.method == "POST":
        # Score against the puzzle the page was rendered from, not whatever
        # today's seed has become since
        seed = views_helper.seed_from_posted_url(request, puzzle_type) or seed
        return views_helper.post_generated_puzzle(request, puzzle_type, seed, page_heading, is_daily=True)

    return views_helper.get_generated_puzzle(request, puzzle_type, seed, page_heading, is_daily=True)


@login_required
def puzzle_view(request, puzzle_date, puzzle_type):

    if request.method == "GET":
        return views_helper.get_puzzle(request, puzzle_type, puzzle_date, f"{puzzle_type.capitalize()}{puzzle_date}")

    if request.method == "POST":
        return views_helper.post_puzzle(request, f"{puzzle_type.capitalize()}{puzzle_date}")


def generated_puzzle_view(request, puzzle_type, seed):
    """Puzzles built by gogenmaker, addressed by generation seed: /uber1, /hyper2..."""

    seed = int(seed)
    page_heading = f"{puzzle_type.capitalize()} {seed}"

    if request.method == "GET":
        return views_helper.get_generated_puzzle(request, puzzle_type, seed, page_heading)

    if request.method == "POST":
        return views_helper.post_generated_puzzle(request, puzzle_type, seed, page_heading)


def difficulty_view(request, puzzle_type):
    """/uber, /ultra and /hyper: jump to the earliest puzzle not yet solved.

    Not login-only: a logged out visitor has completed nothing, so they land
    on the first puzzle rather than being bounced through the login page.
    """

    return views_helper.redirect_to_earliest_incomplete(request, puzzle_type)


@login_required
def leaderboard_view(request):

    users_and_scores = []

    for user in User.objects.all():
        if not user.is_superuser:
            user_puzzle_logs = PuzzleLog.objects.filter(user=user, status='C')
            # Each column counts the archive and the generated puzzles together,
            # so the three of them add up to the total
            counts = [
                user_puzzle_logs.filter(
                    puzzle_type__in=(puzzle_type, views_helper.generated_log_type(puzzle_type))
                ).count()
                for puzzle_type in views_helper.GENERATED_TYPES
            ]
            users_and_scores.append( (user.username, *counts, sum(counts)) )
    
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

        # Anything unrecognised, including the radios being disabled because
        # the notes box is off, means no hints
        fill_hints = request.POST.get("fill_hints")
        valid_hints = [choice for choice, _ in Settings.HINT_CHOICES]

        user_settings.fill_hints = fill_hints if fill_hints in valid_hints else 'N'
        
        
        # If a notes preset is selected. The whole id is taken off the field
        # name, not just its last character, so presets past number 9 work.
        notes_preset = [x for x in request.POST.keys() if x.startswith("notes_preset_")]

        user_settings.preset_notes = None

        if notes_preset:
            preset_id = notes_preset[0].removeprefix("notes_preset_")
            # An id that is not a stored preset means none, rather than a 500
            if preset_id.isdigit():
                user_settings.preset_notes = NoteTemplate.objects.filter(id=preset_id).first()

    user_settings.save()

    presets = NoteTemplate.objects.all()

    return render(
        request=request,
        template_name="gogen/settings.html",
        context={
            'notes_value': user_settings.notes_enabled,
            'hint_choices': Settings.HINT_CHOICES,
            'selected_hints': user_settings.fill_hints,
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
