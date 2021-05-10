import datetime
from constants import DATE_SEPARATOR


def timestamp(date=datetime.datetime.now()):
    """
    Get UNIX timestamp in milliseconds (required by JS)
    """
    return int(date.timestamp() * 1000)


def format_unix_timestamp(millis):
    """
    Format unix timestamp from milliseconds
    """
    return datetime.datetime.fromtimestamp(millis//1000) \
        .strftime('%Y-%m-%d{}%H-%M-%S'.format(DATE_SEPARATOR))
