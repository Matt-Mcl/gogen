#!/bin/bash

source "../venv/bin/activate"

rm -rf htmlcov

export DJANGO_SETTINGS_MODULE=gogensite.settings

coverage run manage.py test gogen.tests.test_views 
coverage run -a manage.py test gogen.tests.test_database
coverage run -a manage.py test gogen.tests.test_models

coverage html
rm .coverage
