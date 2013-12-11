#! /usr/bin/env python
import sys
import re
import os
import logging
import webbrowser
import time
import threading

import requests

from server import Server
from system_tray import system_tray_app

def parse_nxm(nxm_str):
    data = sys.argv[1]
    data = re.sub(r'^nxm:', '', data)
    data = data.strip('/ ')
    _, _, mod_id, _, file_id = data.split('/')
    return mod_id, file_id

def open_when_running(query_url, open_url):
    while True:
        try:
            requests.get('%s/status' % addr)
            webbrowser.open(addr)
            break
        except requests.exceptions.ConnectionError:
            time.sleep(0.5)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    host = 'localhost'
    port = 8080

    addr = 'http://%s:%d' % (host, port)
    if len(sys.argv) > 1:
        mod_id, file_id = parse_nxm(sys.argv[1])

        game = 'skyrim'
        game_id = '110'

        try:
            req = requests.get('%s/status' % addr)
            req = requests.post('%s/download/%s/%s/%s/%s' % (addr, game, game_id, mod_id, file_id))
        except requests.exceptions.ConnectionError:
            pid = os.fork()
            if pid == 0:
                system_tray_app(addr)
            else:
                s = Server()
                s.start_download(game, game_id, mod_id, file_id)
                s.start_server(host, port)
    else:
        status_uri = '%s/status' % addr
        try:
            req = requests.get(status_uri)
            webbrowser.open(addr)
        except requests.exceptions.ConnectionError:
            t = threading.Thread(target=open_when_running,
                                 args=(status_uri, addr,))
            t.daemon = True
            t.start()

            pid = os.fork()
            if pid == 0:
                system_tray_app(addr)
            else:
                Server().start_server(host, port)
