from subprocess import getoutput

DICT_PATH = './dict.txt'

def randomize():
    out = getoutput('sort -R ' + DICT_PATH)
    with open(DICT_PATH, 'w') as f:
        f.write(out)
    f.close()

def getwords():
    randomize()
    out = getoutput('head -n 3 ' + DICT_PATH)
    return '_'.join(out.split('\n')[:3])

if __name__ == '__main__':
    print(getwords())
