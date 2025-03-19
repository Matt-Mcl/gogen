#!/bin/bash

# User must pass in a app when running script
if [ -z "$1" ]; then
    echo "Usage: $0 <app>"
    exit 1
fi

source "../venv/bin/activate"

# Allow a second argument to be passed in to specify the settings file
if [ -z "$2" ]; then
    export DJANGO_SETTINGS_MODULE=gogensite.dev_settings
else
    export DJANGO_SETTINGS_MODULE=gogensite.$2
fi

python3 manage.py makemigrations $1

python3 manage.py migrate $1
