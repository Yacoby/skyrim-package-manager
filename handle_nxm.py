import sys
import json
import os
import shutil
import time
import logging

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


#download_mod_file('skyrim', '110', '98915')
download_mod('skyrim', '110', '1000035623')
#download_mod_file('skyrim', '110', '1000018824')
#print nxm_api.req_file_details('skyrim', '110', '1000018824')

#download_mod_file('skyrim', '110', '1000023481')
#print nxm_api.req_file_details('skyrim', '110', '1000023481')


#if __name__ == '__main__':
#    arg = sys.argv[1]
#
#    arg = arg.strip('/')
#    _, _, mod_id, _, file_id = arg.split('/')



