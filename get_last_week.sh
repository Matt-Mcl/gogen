#!/bin/bash

source venv/bin/activate

python3 -c 'from helper import get_tables; get_tables()'

python3 get_all_puzzle.py uber 7
python3 get_all_puzzle.py ultra 7
python3 get_all_puzzle.py hyper 7

