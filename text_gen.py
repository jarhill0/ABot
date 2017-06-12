import configparser as parser
import os
import random

import helpers


# Original source:
# https://github.com/JackToaster/Reassuring-Parable-Generator/tree/32a64fbfd867decd4b804ceb78396e74180dab53


# load the configuration file
def load_config(config_filename):
    # create a config parser
    config = parser.ConfigParser()
    # read the file
    config.read(config_filename)
    # read the values
    dictionary = {}
    for section in config.sections():
        dictionary[section] = {}
        for option in config.options(section):
            dictionary[section][option] = config.get(section, option).splitlines()

    return dictionary['phrases']


def fix_format(input_string):
    return input_string


# evaluate and replace a string
def evaluate_phrase(input_string, phrases):
    if input_string.find('{') == -1:
        return input_string
    else:
        index1 = input_string.find('{')
        index2 = input_string.find('}')
        key = input_string[index1 + 1:index2]
        phrase = random.choice(phrases[key])
        if phrase == '[none]':
            phrase = ''
        input_string = input_string[:index1] + phrase + input_string[index2 + 1:]
        input_string = fix_format(input_string)
        return evaluate_phrase(input_string, phrases)


# generate a phrase
def gen_phrase(phrases):
    output_string = random.choice(phrases['starter'])
    return evaluate_phrase(output_string, phrases)


def text_gen(number, filename='reassuring.cfg'):
    loaded_config = load_config(os.path.join(helpers.folder_path(), filename))
    out = []
    for i in range(number):
        out.append(gen_phrase(loaded_config))
    return ' '.join(out)


if __name__ == '__main__':
    print(text_gen(10))
