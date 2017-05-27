import time


class Cell:
    def __init__(self):
        self.left = None
        self.right = None
        self.value = 0

    def increment(self):
        if self.value == 255:
            self.value = 0
        else:
            self.value += 1

    def decrement(self):
        if self.value == 0:
            self.value = 255
        else:
            self.value -= 1


def step_right(cell):
    if cell.right is None:
        cell.right = Cell()
        cell.right.left = cell
    return cell.right


def step_left(cell):
    if cell.left is None:
        cell.left = Cell()
        cell.left.right = cell
    return cell.left


def find_closing_bracket(string):
    nested_level = 0

    for i, char in enumerate(string):

        if char == '[':
            nested_level += 1
        elif char == ']':
            nested_level -= 1
            if nested_level == 0:
                return i

    raise ValueError('No closing bracket found')


def find_opening_bracket(string):
    nested_level = 0

    for i, char in enumerate(reversed(string)):

        if char == ']':
            nested_level += 1
        elif char == '[':
            nested_level -= 1
            if nested_level == 0:
                return i

    raise ValueError('No opening bracket found')


def execute(code, input_):
    valid_chars = ['<', '>', '+', '-', '.', ',', '[', ']']
    pointer = Cell()
    code_index = 0
    output_text = ''
    start = time.time()

    while True:
        if code_index < len(code):
            char = code[code_index]
        else:
            break
        if time.time() > start + 10:
            return "Timed out.\nOutput: " + output_text

        if char in valid_chars:

            if char == '<':
                pointer = step_left(pointer)

            elif char == '>':
                pointer = step_right(pointer)

            elif char == '+':
                pointer.increment()

            elif char == '-':
                pointer.decrement()

            elif char == '.':
                output_text += chr(pointer.value)

            elif char == ',':
                try:
                    pointer.value = ord(input_[0]) % 256
                except IndexError:
                    return 'Error. Expected input.'
                finally:
                    input_ = input_[1:]


            elif char == '[':
                if pointer.value == 0:
                    code_index += find_closing_bracket(code[code_index:])

            elif char == ']':
                if pointer.value != 0:
                    code_index -= find_opening_bracket(code[:code_index + 1])

        code_index += 1

    return "Output: " + output_text


def main(my_code, input_=''):
    try:
        return execute(my_code, input_)[:1000]
    except BaseException as e:
        return str(e)


if __name__ == '__main__':
    print(main('random test', input_='hello'))
