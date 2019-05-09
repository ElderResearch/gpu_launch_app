#!/usr/bin/env python3

import argparse
from app import create_app
from app.extensions import db
from app.models import ActivityLog

server = create_app()

@server.shell_context_processor
def make_shell_context():
    return {'db': db, 'ActivityLog': ActivityLog}

def parse_args():
    parser = argparse.ArgumentParser()

    debug = "run server in debug mode"
    parser.add_argument('-d', '--debug', action='store_true', help=debug)

    port = "run server on specified port"
    parser.add_argument('-p', '--port', default=5000, type=int, help=port)

    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    server.run('0.0.0.0', port=args.port, debug=args.debug)
