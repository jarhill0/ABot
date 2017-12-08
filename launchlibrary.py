import datetime
import json
import time

import requests


def refresh(db):
    table = db['launches']

    new_launches = _get_new_agency_launches(121)  # SpaceX's ID
    _process(new_launches, table)  # will insert launches into table based on criteria

    # remove old launches
    current_time = time.time()
    for row in table:
        if row['end'] < current_time:
            table.delete(launch_id=row['launch_id'])


def get_next_launch(db):
    table = db['launches']
    if table.count() == 0:
        return None

    now = time.time()
    launch = None
    launch_time = now * 10

    for row in table:
        start = row['start']
        if start < launch_time:
            launch, launch_time = row, start

    return launch


def build_launch_message(launch):
    if launch is None:
        return None, {'text': 'No upcoming launch found.'}
    name = launch['name']
    launch_time = _format_time_range(launch['start'], launch['end'])
    rocket_name = launch['rocket_name']
    rocket_wiki = launch['rocket_wiki']
    rocket_image = launch['rocket_image']

    videos = json.loads(launch['videos'])
    pads = json.loads(launch['pads'])
    missions = json.loads(launch['missions'])

    pads_formatted = ', '.join('[{}]({})'.format(p['name'], p['wiki_url']) for p in pads)
    missions_formatted = '\n'.join('*{}* ({}): _{}_'.format(m['name'], m['type'], m['description']) for m in missions)
    videos_formatted = '\n'.join(videos)

    message = """
{name} at {launch_time}

Launching [{rocket_name}]({rocket_wiki}) from {pads_formatted}.

Missions:
{missions_formatted}

Video:
{videos_formatted}
""".format(name=name, launch_time=launch_time, rocket_name=rocket_name, rocket_wiki=rocket_wiki,
           pads_formatted=pads_formatted, missions_formatted=missions_formatted, videos_formatted=videos_formatted)
    picture_message = {'photo': rocket_image, 'caption': rocket_name}
    text_message = {'text': message,
                    'parse_mode': 'Markdown',
                    'disable_web_page_preview': True}

    return picture_message, text_message


def _process(launches, table):
    current_time = time.time()

    for launch in launches:
        if launch['westamp'] > current_time and launch['tbdtime'] == 0:  # time is after now, and certain
            entry = dict(name=launch['name'], start=launch['wsstamp'], end=launch['westamp'])
            entry['videos'] = json.dumps(launch['vidURLs'])
            location = launch['location']
            entry['pads'] = json.dumps([{'name': p['name'], 'wiki_url': p['wikiURL']} for p in location['pads']])
            entry['rocket_name'] = launch['rocket']['name']
            entry['rocket_wiki'] = launch['rocket']['wikiURL']
            entry['rocket_image'] = launch['rocket']['imageURL']
            entry['missions'] = json.dumps([{'name': m['name'],
                                             'type': m['typeName'],
                                             'description': m['description']}
                                            for m in launch['missions']])

            entry['launch_id'] = launch['id']
            table.upsert(entry, ['launch_id'])  # insert and update what's there


def _get_new_agency_launches(agency_id):
    url = 'https://launchlibrary.net/1.3/launch/next/'
    num_total = 30
    output = []

    try:
        new_launches = json.loads(requests.get(url + str(num_total)).content.decode('utf-8'))['launches']
    except ValueError:
        # Some API error; let's not bring down the whole bot.
        return []
    for launch in new_launches:
        if any(ag['id'] == agency_id for ag in launch['rocket']['agencies']):
            output.append(launch)

    return output


def _format_time_range(start, end):
    """Return string like '2017–11–22 3:35 PM – 3:42 PM"""
    part1 = datetime.datetime.fromtimestamp(start).strftime('%Y–%m–%d %I:%M %p – ')
    part2 = datetime.datetime.fromtimestamp(end).strftime('%I:%M %p')

    return part1 + part2
