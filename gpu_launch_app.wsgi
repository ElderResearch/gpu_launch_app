#!/usr/env/bin python3

import sys
import logging

logging.basicConfig(stream=sys.stderr)

sys.path.insert(0,"/var/www/gpu_launch_app/")

from app import app as application
