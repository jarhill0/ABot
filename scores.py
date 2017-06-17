import json
import os

import helpers

with open(os.path.join(helpers.folder_path(), 'data', 'scores.json'), 'r') as f:
    scores = json.load(f)


def get_score(id_):
    return scores.setdefault(id_, 0)


def change_score(id_, change):
    scores[id_] += change
    with open(os.path.join(helpers.folder_path(), 'data', 'scores.json'), 'w') as f:
        json.dump(scores, f)
