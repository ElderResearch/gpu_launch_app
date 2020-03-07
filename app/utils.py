import getpass
import hashlib
import random
from datetime import datetime

from ipython_genutils.py3compat import cast_bytes, str_to_bytes

import pytz

salt_len = 12


def _calculate_uptime(t0, t1=None, timezone="US/Eastern"):
    if t1 is None:
        t1 = datetime.now(tz=pytz.timezone(timezone))
    td = t1 - t0
    days, rem = divmod(td.total_seconds(), 86400)
    hours, rem = divmod(rem, 3600)
    minutes, seconds = divmod(rem, 60)
    return days, hours, minutes, seconds


def passwd(passphrase=None, algorithm="sha1"):
    if passphrase is None:
        for i in range(3):
            p0 = getpass.getpass("Enter password: ")
            p1 = getpass.getpass("Verify password: ")
            if p0 == p1:
                passphrase = p0
                break
            else:
                print("Passwords do not match.")
        else:
            raise ValueError("No matching passwords found. Giving up.")

    h = hashlib.new(algorithm)
    salt = ("%0" + str(salt_len) + "x") % random.getrandbits(4 * salt_len)
    h.update(cast_bytes(passphrase, "utf-8") + str_to_bytes(salt, "ascii"))

    return ":".join((algorithm, salt, h.hexdigest()))


def passwd_check(hashed_passphrase, passphrase):
    try:
        algorithm, salt, pw_digest = hashed_passphrase.split(":", 2)
    except (ValueError, TypeError):
        return False

    try:
        h = hashlib.new(algorithm)
    except ValueError:
        return False

    if len(pw_digest) == 0:
        return False

    h.update(cast_bytes(passphrase, "utf-8") + cast_bytes(salt, "ascii"))

    return h.hexdigest() == pw_digest
