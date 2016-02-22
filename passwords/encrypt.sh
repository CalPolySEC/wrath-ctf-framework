#!/bin/sh

# usage: ./decrypt.sh <infile> <outfile>
openssl enc -e -in $1 -out $2 -aes-256-cbc
