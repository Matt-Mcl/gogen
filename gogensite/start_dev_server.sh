#!/bin/bash

source "../venv/bin/activate"

export DJANGO_SETTINGS_MODULE=gogensite.dev_settings

python3 manage.py runserver 0.0.0.0:8080
