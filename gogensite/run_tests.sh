#!/bin/bash

if [ -n "$1" ]; then
    cd $1
fi

source "../venv/bin/activate"

export DJANGO_SETTINGS_MODULE=gogensite.settings

max_retries=10
retry_count=0

while [ $retry_count -lt $max_retries ]; do
    python3 manage.py test gogen.tests.test_views && python3 manage.py test gogen.tests.test_database && python3 manage.py test gogen.tests.test_models
    if [ $? = 0 ]; then
        exit 0
    else
        echo "Some tests failed. Retrying..."
        retry_count=$((retry_count + 1))
    fi
done

echo "Maximum retries reached. Exiting."
exit 1
