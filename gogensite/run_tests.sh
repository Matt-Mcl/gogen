#!/bin/bash

if [ -n "$1" ]; then
    cd $1
fi

source "../venv/bin/activate"

export DJANGO_SETTINGS_MODULE=gogensite.dev_settings

python3 manage.py test
