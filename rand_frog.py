import json
import os
import random

import helpers

frog_path = os.path.join(helpers.folder_path(), 'data', 'frogs.json')
with open(frog_path, 'r') as f:
    frogs = json.load(f)


def main():
    return random.choice(frogs)
