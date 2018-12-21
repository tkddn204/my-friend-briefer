from threading import Timer
from datetime import datetime, timedelta


# https://stackoverflow.com/a/19752594
def set_interval(func, sec):
    def func_wrapper():
        set_interval(func, nine_time())
        func()

    t = Timer(sec, func_wrapper)
    t.start()
    return t


def nine_time():
    now = datetime.now()
    nine = now.replace(hour=9, minute=0, second=0, microsecond=0)
    if now >= nine:
        nine = now + timedelta(days=1)
        result = (nine - now).total_seconds()
    else:
        result = (now - nine).total_seconds()

    return result
