from datetime import datetime

import pytz


def _calculate_uptime(t0, t1=None, timezone="US/Eastern"):
    if t1 is None:
        t1 = datetime.now(tz=pytz.timezone(timezone))
    td = t1 - t0
    days, rem = divmod(td.total_seconds(), 86400)
    hours, rem = divmod(rem, 3600)
    minutes, seconds = divmod(rem, 60)
    return days, hours, minutes, seconds
