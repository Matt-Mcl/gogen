#!/bin/bash

export DJANGO_SETTINGS_MODULE=gogensite.settings

source ../venv/bin/activate

pip install -r ../requirements.txt

python3 manage.py makemigrations

if [ $? -eq 1 ]; then
    echo "Make migrations failed"
    git reset --hard HEAD~1
    exit 1
fi

python3 manage.py migrate

if [ $? -eq 1 ]; then
    echo "Migrations failed"
    git reset --hard HEAD~1
    exit 1
fi

python3 manage.py test

for run in {1..$max_retries}; do
    python3 manage.py test gogen.tests.test_views && python3 manage.py test gogen.tests.test_database && python3 manage.py test gogen.tests.test_models
    if [ $? = 0 ]; then
        exit 0
    fi
done

echo "Maximum retries reached. Exiting."
git reset --hard HEAD~1
exit 1