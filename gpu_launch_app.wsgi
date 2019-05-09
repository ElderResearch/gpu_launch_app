#!/usr/env/bin python3

import os
import sys
import logging
from dotenv import load_dotenv

logging.basicConfig(stream=sys.stderr)

project_path = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_path)
load_dotenv()

from app import create_app

application = create_app()
