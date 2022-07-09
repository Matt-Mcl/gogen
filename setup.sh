#!/bin/bash

if [ ! -d venv ]; then
    echo "venv not present - creating" 
    python3 -m venv venv
    source "venv/bin/activate"

    pip install --upgrade pip
    pip install -r requirements.txt
fi

key=$(< /dev/urandom tr -dc _A-Z-a-z-0-9 | head -c80)
echo "SECRET_KEY=$key" > gogensite/.env
