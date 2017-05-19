import json
import random

with open('data/frogs.json', 'r') as f:
    frogs = json.load(f)['images']


def main():
    return frogs[random.randint(0, len(frogs) - 1)]['url']


if __name__ == '__main__':
    print(main())
