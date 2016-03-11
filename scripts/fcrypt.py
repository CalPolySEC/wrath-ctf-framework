#!/usr/bin/env python3

import subprocess

ENCRYPT="./encrypt.sh"
DECRYPT="./decrypt.sh"
LOCK_PATH="/tmp/pysha_crypt.lock"


def fcrypt(CRYPT, fin, fout, pw):
    subprocess.call([CRYPT, fin, fout, pw])

def encrypt(fin, fout, pw):
    fcrypt(ENCRYPT, fin, fout, pw)

def decrypt(fin, fout, pw):
    fcrypt(DECRYPT, fin, fout, pw)
