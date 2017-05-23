import random


def choice(string):
    items = string.split(';')

    return random.choice(items).strip()


if __name__ == '__main__':
    print(choice(';;;'))
