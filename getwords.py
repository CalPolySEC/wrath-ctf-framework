from subprocess import getoutput
from random import randrange
from filelock import FileLock
import os

LOCK_PATH = '/tmp/wordlist_dict.lock'
DICT_PATH = './dict.txt'

OOPS_SEEK_TOO_FAR = 48


def randomize():
    if getoutput('uname') != "Linux" and 'n' in input("Your OS might not support `sort -R`, proceed? [Yn] "):
        print("Exiting")
        return
    out = getoutput('sort -R ' + DICT_PATH)
    with FileLock(LOCK_PATH):
        with open(DICT_PATH, 'w') as f:
            f.write(out)
        f.close()


def getwords():
    with open(DICT_PATH, 'r') as f:
        f.seek(randrange(0, os.path.getsize(DICT_PATH) - OOPS_SEEK_TOO_FAR))
        out = f.readlines(OOPS_SEEK_TOO_FAR)
        out = [x.replace('\n', '') for x in out]
    return '_'.join(out[1:4])


if __name__ == '__main__':
    randomize()
    print(getwords())
