#!/bin/sh

for filename in data/2025-08-20T2*.bmp
do
    read_gauge data/config.tsv "$filename"
done
