#!/bin/bash

while true; do
    output=$(psql -U postgresmd5 -d gogen -c "select (select count(*) from uber) AS UberCount, (select count(*) from ultra) AS UltraCount, (select count(*) from hyper) AS HyperCount;")
    clear
    printf "$lastoutput"
    printf "\n### old/\ ########### \/new ###\n"
    printf "$output"
    lastoutput=$output
    sleep 10
done
