import json
import random

with open('data/frogs.json', 'r') as f:
    frogs = json.load(f)['images']


def main():
    return random.choice(frogs)['url']


if __name__ == '__main__':
    print(main())
