from bottle import route, run, static_file, install
import logging
import json
import os

from functools import partial

from downloader import DownloadManager
from nxm_register import register_nxm_handler, is_nxm_registered
from server_adapter import StoppableWSGIRefServer
from server_heartbeat import HeartbeatMonitor, Heartbeat

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
def nxm_details():
    return {'registered':is_nxm_registered()}

@route('/nxm/register')
def nxm_register():
    register_nxm_handler()
    return nxm_details()

@route('/')
def index():
    return static_file('index.html', root='gui/')

@route('/static/<filepath:path>')
def server_static(filepath):
    return static_file(filepath, root='gui/')

@route('/shutdown')
def shutdown():
    server.stop()

def local_variable_plugin(to_inject, callback):
    def wrapper(*args, **kwargs):
        f_globals = callback.func_globals
        old_values = {}

        for name, var in to_inject.iteritems():
            try:
                old_values[name] = f_globals[name]
            except KeyError:
                pass
            f_globals[name] = var

        result = callback(*args, **kwargs)

        for key, value in old_values.iteritems():
            f_globals[key] = value

        return result

    return wrapper


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

logging.basicConfig(level=logging.DEBUG)


server = StoppableWSGIRefServer(host='localhost', port=8080)

hb = Heartbeat()
install(partial(local_variable_plugin, {
    'heartbeat': hb,
    'server' : server,
}))


hb_monitor = HeartbeatMonitor(hb, 10, server.stop)
hb_monitor.monitor()

run(server=server)

download_manager.stop()
hb_monitor.stop()
