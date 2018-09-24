import time


class Cell:
    def __init__(self, *, left=None, right=None):
        self._left = left
        self._right = right
        self.value = 0

    def __repr__(self):
        return str(self.value)

    def increment(self):
        self.value = (self.value + 1) % 256

    def decrement(self):
        self.value = (self.value - 1) % 256

    def right(self):
        if self._right is None:
            self._right = Cell(left=self)
        return self._right

    def left(self):
        if self._left is None:
            self._left = Cell(right=self)
        return self._left


class Input:
    def __init__(self, string):
        self._string = string
        self._index = 0

    def get_char(self):
        if self._index >= len(self._string):
            return 0
        retval = ord(self._string[self._index]) % 256
        self._index += 1
        return retval


def match_brackets(string):
    stack = []
    pairs = {}

    for i, char in enumerate(string):
        if char == '[':
            stack.append(i)
        if char == ']':
            if len(stack) == 0:
                raise ValueError('invalid brackets')
            other = stack.pop(-1)
            pairs[other] = i
            pairs[i] = other

    if len(stack) != 0:
        raise ValueError('invalid brackets')
    return pairs


def execute(code, input_):
    pointer = Cell()
    input_ = Input(input_)
    code_index = 0
    bracket_pairs = match_brackets(code)
    output = []
    start = time.time()

    while code_index < len(code):
        char = code[code_index]
        if time.time() > start + 10:
            return 'Timed out.\nOutput:\n' + ''.join(output)

        if char == '<':
            pointer = pointer.left()

        elif char == '>':
            pointer = pointer.right()

        elif char == '+':
            pointer.increment()

        elif char == '-':
            pointer.decrement()

        elif char == '.':
            output.append(chr(pointer.value))

        elif char == ',':
            pointer.value = input_.get_char()

        elif char == '[':
            if pointer.value == 0:
                code_index = bracket_pairs[code_index]

        elif char == ']':
            if pointer.value != 0:
                code_index = bracket_pairs[code_index]

        code_index += 1

    return 'Output:\n' + ''.join(output)


def main(my_code, input_=''):
    # noinspection PyBroadException
    try:
        return execute(my_code, input_)[:4077]
    except Exception:
        return 'Error.'
