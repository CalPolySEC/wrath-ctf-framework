#!/bin/sh

# usage: ./decrypt.sh <infile> <outfile>
openssl enc -d -in $1.enc -out $2.txt -aes-256-cbc
