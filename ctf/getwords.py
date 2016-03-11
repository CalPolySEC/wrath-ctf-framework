from subprocess import getoutput
from random import randrange
from filelock import FileLock
from time import time
import os

LOCK_PATH = '/tmp/wordlist_dict.lock'
DICT_PATH = './dict.txt'
PW_LENGTH = 3


def randomize():
    """ black magic to randomize a dictionary file
        using command-line sort(8)
        Don't worry, we lock the dict file """
    if getoutput('uname') != "Linux" and 'n' in input("Your OS might not support `sort -R`, proceed? [Yn] ").lower():
        print("Exiting")
        return
    out = getoutput('sort -R ' + DICT_PATH)
    with FileLock(LOCK_PATH):
        with open(DICT_PATH, 'w') as f:
            f.write(out)
        f.close()

class PasswordFactory:
    """ Password FACTORY. 
        IT'S A FACTORY. """

    def refresh(self):
        """ delicious randomized steak
            with a side of effects """
        randomize()
        self.passwords = getwords()
        self.remaining = int(len(passwords) / 3)

    def get_pass(self):
        """ Client-facing code, so it
            has to be pretty. Naturally,
            build strings, pop from arrays,
            and generally enterprise around
            while state flies left and right """
        if self.remaining == 0:
            self.refresh()
        pw = ""
        for i in range(PW_LENGTH - 1):
            pw += self.passwords.pop()
            pw += '_'
        pw += self.passwords.pop()
        self.remaining -= 1

def getwords():
    """ Bullshit: pull the ENTIRE FILE
        into memory """
    with open(DICT_PATH, 'r') as f:
        f.readlines()

if __name__ == '__main__':
    randomize()
    print(getwords())
