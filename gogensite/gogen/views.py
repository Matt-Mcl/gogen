from django.shortcuts import render
from django.http import HttpResponse
from django.conf import settings
from copy import deepcopy
import psycopg

def daily_view(request):

    if request.method == "GET":
        with psycopg.connect(settings.PG_CONNECTION) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM uber;")

                daily_uber = cur.fetchone()

                return render(
                    request=request,
                    template_name='puzzle.html',
                    context={
                        'url': daily_uber[0],
                        'words': daily_uber[2],
                        'board': daily_uber[3]
                    }
                )
    

    if request.method == "POST":

        url = list(request.POST.items())[1][1]

        with psycopg.connect(settings.PG_CONNECTION) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM uber;")

                daily_uber = cur.fetchone()

                solution_board = daily_uber[4]

        letters = deepcopy(solution_board)
 
        for item in list(request.POST.items())[2:]:
            letters[int(item[0][0])][int(item[0][1])] = item[1]

        if letters == solution_board:
            return HttpResponse("Correct!")
        else:
            # Loop through each board and keep changes made by user
            for i in range(0, 5):
                for j, v in enumerate(zip(letters[i], daily_uber[3][i])):
                    if v[0] != v[1]:
                        letters[i][j] = f"*{letters[i][j]}"

            return render(
                request=request,
                template_name='puzzle.html',
                context={
                    'url': daily_uber[0],
                    'words': daily_uber[2],
                    'board': letters,
                    'mistake': True
                }
            )