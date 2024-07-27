FROM python:3.12

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY ./gogensite .

EXPOSE 8002

CMD ["python3", "manage.py", "migrate"]

CMD ["python3", "manage.py", "collectstatic"]

CMD ["gunicorn", "-b", "0.0.0.0:8002", "gogensite.wsgi:application", "--log-level=debug", "--error-logfile=/app/error.log", "--access-logfile=/app/error.log"]
