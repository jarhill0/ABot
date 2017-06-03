import sched
import threading
import time

from config import a_group_id
from launchlibrary import load_launch_info_from_disk
from main import send_launch_message, restart


def get_next_launch():
    json_data = load_launch_info_from_disk()
    return json_data['launches'][0]


def send_automated_message(launch, triggertime):
    # ensure we are within a minute of the intended trigger time so as not to re-trigger messages upon script restart
    if abs(time.time() - triggertime) < 60:
        send_launch_message(launch, a_group_id)
        time.sleep(70)
        if time.time() + 120 > launch['wsstamp']:
            restart()


def set_launch_triggers(launch):
    start_time = launch['wsstamp']
    alert_times = {
        0: start_time,
        1: start_time - (60 * 60),
        4: start_time - (60 * 60 * 4),
        24: start_time - (60 * 60 * 24)
    }

    scheduler = sched.scheduler(time.time, time.sleep)
    t = threading.Thread(target=scheduler.run)

    for key in alert_times.keys():
        scheduler.enterabs(alert_times[key], 1, send_automated_message, (launch, alert_times[key]))

    t.start()
