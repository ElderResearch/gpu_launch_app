#!/usr/bin/python3

import random
import secrets
from datetime import datetime, timedelta
from numpy.random import exponential

def generate_usage_log_data(Model, n=100):
    _names = ['andy','betty', 'bobby', 'timmy','sue']
    _imagetypes = ['Python', 'Python+R']
    _numgpus =[0,1,2,3,4]
    containers = []

    for i in range(n):
        td_start = timedelta(days=i % 30, hours=random.randint(0,23))
        start = datetime.utcnow() - td_start
        instance = Model(id=secrets.token_hex(32),
                         username=random.choice(_names),
                         image_type=random.choice(_imagetypes),
                         num_gpus=random.choice(_numgpus),
                         start_time=start,
                         stop_time=start + timedelta(hours=exponential(8)))
        containers.append(instance)

    return containers
