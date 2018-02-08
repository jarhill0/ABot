import os.path

import dataset

import helpers

db = dataset.connect('sqlite:///{}'.format(os.path.join(helpers.folder_path(), 'data', 'mydatabase.db')))
