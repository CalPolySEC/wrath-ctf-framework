#!/bin/sh

# usage: ./decrypt.sh <infile> <outfile> <pass>
openssl enc -e -in $1.txt -out $2.enc -pass $3 -aes-256-cbc
