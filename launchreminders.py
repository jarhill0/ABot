
from launchlibrary import load_launch_info_from_disk
from main import send_launch_message, schedule_launches


class NoLaunchFoundError(IndexError):
    pass


def get_next_launch():
    json_data = load_launch_info_from_disk()
    try:
        return json_data['launches'][0]
    except IndexError:
        raise NoLaunchFoundError


def send_automated_message(launch, subscriptions):
    for chat_id in subscriptions.get_subscribers('launches'):
        send_launch_message(launch, chat_id)


def set_launch_triggers(launch, schedule, subscriptions):
    start_time = launch['wsstamp']
    alert_times = [start_time, start_time - (60 * 60), start_time - (60 * 60 * 4), start_time - (60 * 60 * 24)]
    for alert_time in alert_times:
        schedule.add_event(alert_time, send_automated_message, args=[launch, subscriptions], execute_past=False)
    schedule.add_event(start_time + 60 * 60, schedule_launches, args=[schedule])  # refresh after a launch has started
