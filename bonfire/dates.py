import time
from datetime import datetime, timedelta

TWITTER_TIME_FORMAT = '%a %b %d %H:%M:%S +0000 %Y'
ELASTICSEARCH_TIME_FORMAT = 'EEE MMM d HH:mm:ss Z yyyy'
DATETIMEPICKER_TIME_FORMAT = '%Y/%m/%d %H:%M'


def now(stringify=False):
    """Return now.
    :arg stringify: return now as a formatted string."""
    now = datetime.utcnow()
    if stringify:
        return stringify_date(now)
    return now


def apply_offset(start_date, offset):
    """Apply an offset in minutes to a given date."""
    return start_date + timedelta(minutes=offset)


def get_query_dates(start, end, hours=None, stringify=True):
    """
    Gets the start and end dates for a query.
    :arg start: datetime to start with.
        If not present, defaults to since argument.
    :arg end: datetime to end with.
        If not present, defaults to now.
    :arg hours: number of hours since end to start with,
        if no start is specified.
    :arg stringify: return as formatted strings.
    """
    if not end:
        end = now()
    if not start:
        start = end - timedelta(hours=hours)
    if stringify:
        start = stringify_date(start)
        end = stringify_date(end)
    return start, end


def stringify_date(dt):
    """Convert a datetime to an elasticsearch-formatted datestring (UTC)."""
    return dt.strftime(TWITTER_TIME_FORMAT) if dt else ''


def dateify_string(datestr, format=TWITTER_TIME_FORMAT):
    """Convert a date string to a python datetime (UTC)."""
    return datetime.strptime(datestr, TWITTER_TIME_FORMAT) if datestr else None


def get_since_now(start_time, time_type=None, stringify=True):
    """
    Gets the amount of time that has expired since now.
    Smartly chooses between hours, days, minutes, and seconds.
    Accepts datetime, unix epoch, or Twitter-formatted datestring.

    :arg time_type: force return of a certain time measurement
        (e.g. "120 seconds ago" instead of "2 minutes ago")
    :arg stringify: turn result into a string instead of tuple,
        pluralized if need be
    """
    response = None

    if isinstance(start_time, (int, float)):
        start_time = epoch_to_datetime(start_time)
    elif isinstance(start_time, basestring):
        start_time = dateify_string(start_time)
    diff = int((now() - start_time).total_seconds())

    time_types = (
        ('day', diff / 60 / 60 / 24),
        ('hour', diff / 60 / 60),
        ('minute', diff / 60),
        ('second', diff)
    )
    if time_type is not None:
        response = (dict(time_types)[time_type], time_type)

    else:
        # Loop through each amount, and if there are any, get its value
        for word, amt in time_types:
            if amt:
                response = (amt, word)
                break
        # Since it goes down to seconds, you probably shouldn't get here
        if response is None:
            response = (0, 'second')
    if stringify:
        response = stringify_since_now(*response)
    return response


def epoch_to_datetime(epoch):
    """Converts unix timestamp to python datetime (UTC)."""
    return datetime(*time.gmtime(epoch / 1000)[:7])


def stringify_since_now(amt, time_type):
    """Takes an amount and a type. Returns a pluralized string."""
    response = str(amt) + ' ' + time_type
    if amt == 1:
        return response
    return response + 's'
