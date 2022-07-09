#!/bin/bash

sudo -u postgres dropdb django_gogensite_dev
sudo -u postgres createdb django_gogensite_dev -T django_gogensite
