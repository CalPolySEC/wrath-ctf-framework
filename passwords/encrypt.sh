#!/bin/sh

# usage: ./decrypt.sh <infile> <outfile>
openssl enc -e -in $1.txt -out $2.enc -aes-256-cbc
