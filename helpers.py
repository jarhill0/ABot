import os


def folder_path():
    return os.path.dirname(os.path.abspath(__file__))


class SubscriptionNotFoundError(Exception):
    pass


class Subscriptions:
    def __init__(self, topics, db):
        self.table = db['subscriptions']
        self.topics = topics

    def __repr__(self):
        return 'Subscriptions({})'.format(self.topics)

    def subscribe(self, topic, chat_id):
        if topic not in self.topics:
            raise SubscriptionNotFoundError
        self.table.insert_ignore(dict(topic=topic, chat=chat_id), ['topic', 'chat'])

    def unsubscribe(self, topic, chat_id):
        if topic not in self.topics:
            raise SubscriptionNotFoundError
        self.table.delete(chat=chat_id, topic=topic)

    def get_subscribers(self, topic):
        if topic not in self.topics:
            raise SubscriptionNotFoundError
        for subscriber in self.table.find(topic=topic):
            yield subscriber['chat']  # expecting an int, I think

    def my_subscriptions(self, chat_id):
        for subscription in self.table.find(chat=chat_id):
            yield subscription['topic']
