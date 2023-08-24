#!/bin/bash

export DJANGO_SETTINGS_MODULE=gogensite.settings

source ../venv/bin/activate

pip install -r ../requirements.txt

if [ $? -eq 1 ]; then
    echo "Pull failed"
    exit 1
fi

python3 manage.py migrate

if [ $? -eq 1 ]; then
    echo "Migrations failed"
    git reset --hard HEAD~1
    exit 1
fi

python3 manage.py test

if [ $? -eq 1 ]; then
    echo "Tests failed"
    git reset --hard HEAD~1
    exit 1
else
    sudo systemctl restart gogen-site.service
fi
