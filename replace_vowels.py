VOWELS = 'aeiou'
SUB = 'y'


def replace(words):
    return ''.join(SUB.lower() if l in VOWELS.lower() else SUB.upper() if l in VOWELS.upper() else l for l in words)
