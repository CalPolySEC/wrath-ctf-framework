#!/bin/sh

# usage: ./decrypt.sh <infile> <outfile> <pass>
openssl enc -d -in $1.enc -out $2.txt -pass $3 -aes-256-cbc
