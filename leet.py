"""1234567890"""

TRANS = {'A': '4',
         'B': '8',
         'E': '3',
         'G': '6',
         'I': '1',
         'O': '0',
         'S': '5',
         'T': '7',
         'Y': '2',
         'b': '8',
         'e': '3',
         'g': '9',
         'l': '1',
         'o': '0',
         's': '5',
         't': '7',
         'z': '2'}


def leet(message):
    return ''.join(TRANS.get(l, l) for l in message)
