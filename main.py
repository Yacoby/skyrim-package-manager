#! /usr/bin/env python
import sys
import re
import os
import logging
import logging.handlers
import webbrowser
import time
import threading
import multiprocessing
import argparse

import requests

from server import Server
from system_tray import system_tray_app
from nxm_register import register_nxm_handler

def parse_nxm(nxm_str):
    data = re.sub(r'^nxm:', '', nxm_str)
    data = data.strip('/ ')
    _, _, mod_id, _, file_id = data.split('/')
    return mod_id, file_id

def open_when_running(query_url, open_url):
    '''
    TODO this is terrible.
    '''
    while True:
        try:
            requests.get(query_url)
            webbrowser.open(open_url)
            break
        except requests.exceptions.ConnectionError:
            time.sleep(0.5)

if __name__ == '__main__':
    #TODO path name problem when frozen
    LOG_FILE = os.path.join(os.path.dirname(__file__), 'log')
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger()
    logger.addHandler(logging.StreamHandler())
    logger.addHandler(logging.handlers.RotatingFileHandler(
        LOG_FILE, maxBytes=(1048576*5), backupCount=7
    ))


    #registering nxm is a feature here to allow for permission elevation
    parser = argparse.ArgumentParser()
    parser.add_argument('nxm', nargs='?')
    parser.add_argument('--regnxm',
                        dest='regnxm',
                        action='store_const',
                        const=True,
                        default=False)
    args = parser.parse_args()

    if args.regnxm:
        register_nxm_handler()
        sys.exit(0)

    host = 'localhost'
    port = 8080

    addr = 'http://%s:%d' % (host, port)
    status_uri = '%s/status' % addr
    if args.nxm:
        mod_id, file_id = parse_nxm(args.nxm)

        game = 'skyrim'
        game_id = '110'

        try:
            req = requests.get(status_uri)
            req = requests.post('%s/download/%s/%s/%s/%s' % (addr, game, game_id, mod_id, file_id))
        except requests.exceptions.ConnectionError:
            p = multiprocessing.Process(target=system_tray_app, args=(addr,))
            p.start()
            s = Server()
            s.start_download(game, game_id, mod_id, file_id)
            s.start_server(host, port)
            p.terminate()
    else:
        try:
            req = requests.get(status_uri)
            webbrowser.open(addr)
        except requests.exceptions.ConnectionError:
            t = threading.Thread(target=open_when_running,
                                 args=(status_uri, addr,))
            t.daemon = True
            t.start()

            p = multiprocessing.Process(target=system_tray_app, args=(addr,))
            p.start()
            Server().start_server(host, port)
            p.terminate()
