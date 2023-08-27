#!/bin/bash

export DJANGO_SETTINGS_MODULE=gogensite.settings

if [ ! -d venv ]; then
    echo "venv not present - creating" 
    python3 -m venv venv
    source "venv/bin/activate"

    pip install --upgrade pip
    pip install -r requirements.txt
fi

cd gogensite

cp ../../dev-gogen-app/gogensite/.env .env

python3 manage.py makemigrations

if [ $? -eq 1 ]; then
    echo "Make migrations failed"
    exit 1
fi

python3 manage.py migrate

if [ $? -eq 1 ]; then
    echo "Migrations failed"
    exit 1
fi

retry_count=0
max_retries=5

while [ $retry_count -lt $max_retries ]; do
    python3 manage.py test gogen.tests.test_views --noinput && python3 manage.py test gogen.tests.test_database --noinput && python3 manage.py test gogen.tests.test_models --noinput
    if [ $? = 0 ]; then
        exit 0
    else
        echo "Some tests failed. Retrying..."
        retry_count=$((retry_count + 1))
    fi
done

echo "Maximum retries reached. Exiting."
exit 1