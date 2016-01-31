from subprocess import getoutput
from random import randrange

DICT_PATH = './dict.txt'

OOPS_SEEK_TOO_FAR = 48

# don't run on OS X
def randomize():
    out = getoutput('sort -R ' + DICT_PATH)
    with open(DICT_PATH, 'w') as f:
        f.write(out)
    f.close()

def getwords():
    with open(DICT_PATH, 'r') as f:
        f.seek(randrange(0, int(getoutput('wc -l ' + DICT_PATH).split(' ')[0])-OOPS_SEEK_TOO_FAR))
        out = f.readlines(OOPS_SEEK_TOO_FAR)
        out = [x.replace('\n', '') for x in out]
    print(out)
    return '_'.join(out[1:4])

if __name__ == '__main__':
    print(getwords())
