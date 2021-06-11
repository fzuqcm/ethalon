import datetime
import time

from constants import DATE_SEPARATOR


def timestamp(date=datetime.datetime.now()):
    """
    Get UNIX timestamp in milliseconds (required by JS).
    """
    return int(date.timestamp() * 1000)


def format_unix_timestamp(millis):
    """
    Format unix timestamp from milliseconds.
    """
    return datetime.datetime.fromtimestamp(millis//1000) \
        .strftime('%Y-%m-%d{}%H-%M-%S'.format(DATE_SEPARATOR))


def sleep_time():
    """
    Return time in milliseconds to the mearest whole second.
    """
    return (999 - round(time.time() * 1000) % 1000) / 1000
