import random


def choice(items):
    items = items.split(';')

    while '' in items:
        items.remove('')

    return random.choice(items).strip()


if __name__ == '__main__':
    print(choice('Thing 1;Thing 2; Thing 3'))
