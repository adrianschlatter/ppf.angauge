#!/bin/sh

for filename in data/2025-08-20T2*.jpg
do
    read_meter data/config.tsv "$filename"
done
