from django.shortcuts import render
from django.http import HttpResponse
from django.conf import settings
from copy import deepcopy
import psycopg

def test_view(request):

    if request.method == "GET":
        with psycopg.connect(settings.PG_CONNECTION) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM uber;")

                test = cur.fetchone()

                return render(
                    request=request,
                    template_name='test.html',
                    context={
                        'url': test[0],
                        'words': test[2],
                        'board': test[3]
                    }
                )
    

    if request.method == "POST":

        url = list(request.POST.items())[1][1]

        with psycopg.connect(settings.PG_CONNECTION) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM uber;")

                test = cur.fetchone()

                solution_board = test[4]

        letters = deepcopy(solution_board)

        
        print(solution_board)

        for item in list(request.POST.items())[2:]:
            letters[int(item[0][0])][int(item[0][1])] = item[1]

        print(letters)

        print(letters == solution_board)
        
        

        return HttpResponse("")
