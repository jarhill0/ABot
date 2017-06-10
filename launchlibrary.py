import json
import os
import time

import requests

import helpers

filepath = os.path.join(helpers.folder_path(), 'data', 'launches.json')


def filter_upcoming(launches):
    current_time = time.time()
    later_launches = []

    for launch in launches:
        if launch['wsstamp'] > current_time and launch['tbdtime'] == 0:
            later_launches.append(launch)

    return sorted(later_launches, key=lambda k: k['wsstamp'])


def load_launch_info_from_disk():
    with open(filepath, 'r') as f:
        json_data = json.load(f)

    return json_data


def update_json_on_disk():
    json_data = load_launch_info_from_disk()

    try:
        del json_data['offset']
    except KeyError:
        pass

    json_data['launches'] = get_new_agency_launches(121)
    json_data['launches'] = filter_upcoming(json_data['launches'])

    json_data['total'] = len(json_data['launches'])
    json_data['count'] = len(json_data['launches'])

    with open(filepath, 'w') as f:
        json.dump(json_data, f)


def get_new_agency_launches(agency_id):
    url = 'https://launchlibrary.net/1.2/launch/next/'
    num_total = 30
    output = []

    new_launches = json.loads(requests.get(url + str(num_total)).content.decode('utf-8'))['launches']
    for launch in new_launches:
        for agency in launch['rocket']['agencies']:
            if agency['id'] == agency_id:
                output.append(launch)

    return output


if __name__ == '__main__':
    update_json_on_disk()
