#!/bin/sh

# usage: ./decrypt.sh <infile> <outfile>
openssl enc -d -in $1 -out $2.txt -aes-256-cbc
