from subprocess import getoutput
from random import randrange
from filelock import FileLock
from time import time
import os

LOCK_PATH = '/tmp/wordlist_dict.lock'
DICT_PATH = './dict.txt'


def randomize():
    if getoutput('uname') != "Linux" and 'n' in input("Your OS might not support `sort -R`, proceed? [Yn] ").lower():
        print("Exiting")
        return
    out = getoutput('sort -R ' + DICT_PATH)
    with FileLock(LOCK_PATH):
        with open(DICT_PATH, 'w') as f:
            f.write(out)
        f.close()

class PasswordFactory:
    def refresh(self):
        randomize()
        self.passwords = getwords()
        self.remaining = int(len(passwords) / 3)

    def get_pass(self):
        if self.remaining == 0:
            self.refresh()
        pw = ""
        for i in range(2):
            pw += self.passwords.pop()
            pw += '_'
        pw += self.passwords.pop()
        self.remaining -= 1

def getwords():
    with open(DICT_PATH, 'r') as f:
        f.readlines()

if __name__ == '__main__':
    randomize()
    print(getwords())
