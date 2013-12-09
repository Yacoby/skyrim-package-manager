from bottle import route, run, static_file
import logging
import json
import os

from downloader import DownloadManager

with open('cfg.json') as json_fp:
    cfg = json.load(json_fp)
cfg['download_location'] = os.path.abspath(os.path.expanduser(cfg.get('download_location', '')))

try:
    with open('data.json') as json_fp:
        user_data = json.load(json_fp)
except IOError:
    logging.warning('No user data')
    user_data = {}

download_manager = DownloadManager(cfg['user'],
                                   cfg['password'],
                                   user_data.get('session_id'))

@route('/downloading')
def downloading():
    data = []
    for dl in download_manager.get_downloading():
        data.append(dl.raw_data())
    return {'active_downloads':data}

@route('/download/<game>/<game_id>/<mod_id>/<file_id>')
def download(game, game_id, mod_id, file_id):
    download_manager.download(game, game_id, mod_id, file_id)
    return {}

@route('/status')
def status():
    return {
        'running':True,
        'username_set':cfg.get('user', '') != '',
        'password_set':cfg.get('password', '') != '',
        'save_location':cfg['download_location'],
    }

@route('/nxm')
def nxm_details(name):
    return {'registered':True}

@route('/stop')
def stop(name):
    return download_manager.stop()

@route('/')
def index():
    return static_file('index.html', root='gui/')

@route('/static/<filepath:path>')
def server_static(filepath):
    return static_file(filepath, root='gui/')

logging.basicConfig(level=logging.DEBUG)
run(host='localhost', port=8080)
download_manager.stop()
