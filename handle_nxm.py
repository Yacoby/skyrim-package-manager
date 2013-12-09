import sys
import json
import os
import shutil
import time
import logging
import select
import socket

from threading import Thread
from functools import partial

import requests
import progressbar

import nxm_api

logging.basicConfig(level=logging.DEBUG)

def get_dl_url(game, game_id, download_id):
    '''
    Well, when I say best I mean one with the least users. Ideally the API
    would be able to give me the best (like min users, response time etc)
    but this doesn't seem to be a feature
    '''
    server_listing = nxm_api.req_servers(game, game_id, download_id)
    non_premium = (server for server in server_listing if server['IsPremium'] == False)
    try:
        min_user_server = min(non_premium, key=lambda s:s['ConnectedUsers'])
        return min_user_server['URI']
    except ValueError:
        raise ValueError("No servers available")

def _download_and_check_file(session_id, download_location, game, game_id, file_id):
    file_details = nxm_api.req_file_details(game, game_id, file_id)
    download_url = get_dl_url(game, game_id, file_id)

    print(file_details['name'])
    expected_size_bytes = file_details['size']*1024
    widgets = [progressbar.Bar('=', '[', ']'),
               ' ',
               progressbar.Percentage(),
               ' ',
               progressbar.ETA(),
               ' ',
               progressbar.FileTransferSpeed() ]
    bar = progressbar.ProgressBar(maxval=expected_size_bytes + 1024, widgets=widgets)

    path = nxm_api.download(session_id,
                            download_url,
                            bar.update)

    bar.finish()

    expected_size_kb = file_details['size']
    size_kb = os.path.getsize(path)/1024
    if expected_size_kb == size_kb:
        shutil.copy(path, os.path.join(download_location, file_details['name']))
        return True
    else:
        return False

def download_mod(game, game_id, file_id):
    with open('cfg.json') as json_fp:
        cfg = json.load(json_fp)

    try:
        with open('data.json') as json_fp:
            user_data = json.load(json_fp)
    except IOError:
        logging.warning('No user data')
        user_data = {}

    try:
        stored_session_id = session_id = user_data['session_id']
    except KeyError:
        logging.info('No session id found in file')
        stored_session_id = session_id = None

    dl_f = partial(_download_and_check_file,
                   session_id,
                   cfg['download_location'],
                   game,
                   game_id,
                   file_id)
    has_downloaded = dl_f()
    if not has_downloaded:
        logging.info('Failed to download')
        if session_id == None or not nxm_api.is_session_id_valid(session_id):
            logging.info('Attempting login')
            session_id = nxm_api.session_id(cfg['user'], cfg['password'])
            dl_f()

    if session_id != stored_session_id:
        logging.info('Saving new session id')
        user_data['session_id'] = session_id
        with open('data.json', 'w') as json_fp:
            json.dump(user_data, json_fp)

class SocketListener(Thread):

    def __init__(self, queue, address):
        self._queue = queue
        self._address = address
        self._stop = False
        super(SocketListener, self).__init__()

    def stop(self):
        self._stop = True

    def run(self):
        soc = socket.socket(socket.AF_INET)
        soc.bind(self._address)
        soc.listen(5)

        read_list = [soc]
        while not self._stop:
            readable, writable, errored = select.select(read_list, [], [], 0.1)
            for s in readable:
                if s is soc:
                    client_socket, address = soc.accept()
                    read_list.append(client_socket)
                    logging.debug('Socket got connection from <%s, %d>' % address)
                else:
                    data = s.recv(1024)
                    if data:
                        logging.debug('Socket read <%s>' % data)
                        self._queue.append(data.split('\t'))
                    else:
                        logging.debug('Socket closed')
                        s.close()
                        read_list.remove(s)
        soc.close()

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    data = sys.argv[1]
    data = data.strip('/')
    _, _, mod_id, _, file_id = data.split('/')

    address = ('localhost', 6004)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect(address)
        sock.send('\t'.join(('skyrim', '110', file_id)))
        sock.close()
    except socket.error:
        queue = [('skyrim', '110', file_id)]
        listener = SocketListener(queue, address)

        try:
            listener.start()
            while queue:
                game, game_id, file_id = queue.pop()
                download_mod(game, game_id, file_id)
        finally:
            listener.stop()
